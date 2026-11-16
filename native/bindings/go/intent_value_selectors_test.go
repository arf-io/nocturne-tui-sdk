package native

import (
	"bytes"
	"encoding/json"
	"reflect"
	"testing"
)

// TestIntentValueSelectorUsesOldestMatchingRetainedIntent crosses the real C ABI.
// Expected provenance is authored independently of the returned queue/candidate.
func TestIntentValueSelectorUsesOldestMatchingRetainedIntent(t *testing.T) {
	type IntentRecord struct {
		ID              uint64  `json:"id"`
		Event           string  `json:"event"`
		MessageID       uint32  `json:"messageId"`
		ActionID        uint32  `json:"actionId"`
		MessageSequence uint64  `json:"messageSequence"`
		AtUs            uint64  `json:"atUs"`
		Value           float64 `json:"value"`
	}
	type TriggerRecord struct {
		ID               uint32        `json:"id"`
		ConditionNodes   uint32        `json:"conditionNodes"`
		Event            string        `json:"event"`
		FireCount        uint32        `json:"fireCount"`
		LastFireUs       uint64        `json:"lastFireUs"`
		LastIntent       uint64        `json:"lastIntent"`
		PendingIntent    uint64        `json:"pendingIntent"`
		ValueSource      string        `json:"valueSource"`
		IntentCandidate  *IntentRecord `json:"intentCandidate"`
		LastIntentSource *IntentRecord `json:"lastIntentSource"`
	}
	type SceneInfo struct {
		Values   map[string]float64 `json:"values"`
		Intents  []IntentRecord     `json:"intents"`
		Triggers []TriggerRecord    `json:"triggers"`
	}

	scene, err := New(2030)
	if err != nil {
		t.Fatal(err)
	}
	defer scene.Close()
	command := func(raw string) {
		t.Helper()
		if _, err := scene.CommandRaw([]byte(raw)); err != nil {
			t.Fatalf("command %s: %v", raw, err)
		}
	}
	advance := func(atUs uint64) {
		t.Helper()
		if err := scene.AdvanceTo(atUs); err != nil {
			t.Fatal(err)
		}
	}
	info := func() SceneInfo {
		t.Helper()
		raw, err := scene.Info()
		if err != nil {
			t.Fatal(err)
		}
		var value SceneInfo
		if err := json.Unmarshal(raw, &value); err != nil {
			t.Fatal(err)
		}
		return value
	}
	snapshot := func() []byte {
		t.Helper()
		raw, err := scene.Snapshot()
		if err != nil {
			t.Fatal(err)
		}
		return raw
	}

	unrelated := IntentRecord{1, "/parity/unrelated", 40, 3, 1, 100000, 7}
	matching := IntentRecord{2, "/parity/approved", 600, 9, 2, 200000, 7}
	expectedQueue := []IntentRecord{unrelated, matching}
	checkState := func(fired bool) {
		t.Helper()
		value := info()
		if !reflect.DeepEqual(value.Intents, expectedQueue) {
			t.Fatalf("intent retention/provenance: got %+v, want %+v", value.Intents, expectedQueue)
		}
		if len(value.Triggers) != 1 {
			t.Fatalf("expected one trigger, got %+v", value.Triggers)
		}
		rule := value.Triggers[0]
		if rule.ID != 11 || rule.ConditionNodes != 3 || rule.Event != matching.Event || rule.ValueSource != "constant" || rule.PendingIntent != 0 {
			t.Fatalf("wrong trigger identity/grammar/action: %+v", rule)
		}
		wantGuard, wantTarget := float64(0), float64(10)
		wantFireCount, wantLastIntent, wantLastFireUs := uint32(0), uint64(0), uint64(0)
		var wantCandidate, wantAccepted *IntentRecord = &matching, nil
		if fired {
			wantGuard, wantTarget = 1, 13 // Constant increment 3, not payload assignment/addition.
			wantFireCount, wantLastIntent, wantLastFireUs = 1, matching.ID, 300000
			wantCandidate, wantAccepted = nil, &matching
		}
		if guard, ok := value.Values["/parity/enabled"]; !ok || guard != wantGuard {
			t.Fatalf("scalar guard: %+v", value.Values)
		}
		if target, ok := value.Values["/parity/out"]; !ok || target != wantTarget {
			t.Fatalf("constant target update: %+v", value.Values)
		}
		if rule.FireCount != wantFireCount || rule.LastIntent != wantLastIntent || rule.LastFireUs != wantLastFireUs {
			t.Fatalf("fire/watermark advanced incorrectly: %+v", rule)
		}
		if !reflect.DeepEqual(rule.IntentCandidate, wantCandidate) || !reflect.DeepEqual(rule.LastIntentSource, wantAccepted) {
			t.Fatalf("wrong selected/accepted source: candidate=%+v accepted=%+v", rule.IntentCandidate, rule.LastIntentSource)
		}
	}
	checkPure := func(fired bool) {
		t.Helper()
		before := snapshot()
		for index := 0; index < 3; index++ {
			checkState(fired)
			if !bytes.Equal(before, snapshot()) {
				t.Fatal("Info mutated authoritative state")
			}
			frame, err := scene.Render()
			if err != nil || len(frame.Bytes) == 0 {
				t.Fatalf("native render failed: %v", err)
			}
			if !bytes.Equal(before, snapshot()) {
				t.Fatal("Render mutated authoritative state")
			}
		}
		checkState(fired)
	}

	command(`{"op":"define","path":"/parity/enabled","value":0}`)
	command(`{"op":"define","path":"/parity/out","value":10}`)
	command(`{"op":"trigger","id":11,"event":"/parity/approved","when":{"all":[{"path":"/parity/enabled","comparison":"equal","value":1},{"intentValue":{"comparison":"at-least","value":7}}]},"target":"/parity/out","action":"increment","value":3}`)
	initial := info()
	if len(initial.Triggers) != 1 || initial.Triggers[0].IntentCandidate != nil || len(initial.Intents) != 0 {
		t.Fatal("a new scene must have no candidate or retained intentions")
	}
	advance(100000)
	command(`{"op":"status","id":40,"area":0,"text":"Unrelated","durationMs":0,"actions":[{"id":3,"label":"Confirm","event":"/parity/unrelated","value":7}]}`)
	command(`{"op":"notification-action","id":40,"actionId":3}`)
	advance(200000)
	command(`{"op":"status","id":600,"area":0,"text":"Matching","durationMs":0,"actions":[{"id":9,"label":"Confirm","event":"/parity/approved","value":7}]}`)
	command(`{"op":"notification-action","id":600,"actionId":9}`)
	checkPure(false)
	advance(300000) // Time alone cannot release the closed scalar guard.
	checkPure(false)
	command(`{"op":"set","path":"/parity/enabled","value":1}`)
	checkPure(true)
	command(`{"op":"set","path":"/parity/enabled","value":1}`)
	advance(400000)
	checkPure(true) // Accepted intent is still retained, but cannot fire again.
}
