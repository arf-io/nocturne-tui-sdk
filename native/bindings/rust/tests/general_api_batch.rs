use nocturne_native::NativeScene;

#[test]
fn runtime_discovery_agrees_with_wire_writer() {
 let mut s=NativeScene::new(42).unwrap();let saved=s.snapshot().unwrap();let info=s.info();
 for (field,offset) in [("abiVersion",8),("snapshotSchema",12),("sourceSchema",28)]{
  let value=u32::from_le_bytes(saved[offset..offset+4].try_into().unwrap());
  assert!(info.contains(format!(r#""{field}":{value}"#).as_str()),"runtime discovery {field}");
 }
 assert!(info.contains(format!(r#""snapshotCapacityBytes":{}"#,saved.len()).as_str()));
 assert!(info.contains(r#""metadataProfile":"nocturne.metadata/v1""#));
 assert!(info.contains(r#""commandProfile":"nocturne.commands/v1""#));
 assert!(info.contains(r#""character-cell-inspection""#));
 assert_eq!(s.snapshot().unwrap(),saved);s.restore(&saved).unwrap();assert_eq!(s.info(),info);
}

#[test]
fn panel_metadata_preserves_source_and_bound_geometry() {
 for (family,command,expected) in [
  ("window",r#"{"op":"window","id":1,"width":2000000000,"height":1000000000,"title":"NOC 日本","durationMs":1200}"#,vec![r#""width":2000000000"#,r#""height":1000000000"#,r#""title":"NOC 日本"#,r#""durationUs":1200000"#]),
  ("area",r#"{"op":"area","id":1,"width":2147483647,"height":2147483647,"layout":"queue","hideEmpty":true,"fadeMs":500}"#,vec![r#""width":2147483647"#,r#""height":2147483647"#,r#""layout":"queue"#,r#""hideEmpty":true"#,r#""fadeUs":500000"#])
 ]{
  let mut s=NativeScene::new(42).unwrap();s.command(command).unwrap();let saved=s.snapshot().unwrap();let info=s.info();
  for property in &expected{assert!(info.contains(*property),"missing {family} property {property}");}
  assert_eq!(s.snapshot().unwrap(),saved);s.restore(&saved).unwrap();assert_eq!(s.info(),info);
  s.command(&format!(r#"{{"op":"define","path":"/width","value":1234,"binding":{{"family":"{family}","id":1,"field":"width"}}}}"#)).unwrap();
  s.command(r#"{"op":"remove-value","path":"/width"}"#).unwrap();assert!(s.info().contains(r#""width":1234"#));assert!(info.contains(expected[0]));
 }
}

#[test]
fn widget_metadata_preserves_authored_source_and_owned_query() {
 let mut s=NativeScene::new(42).unwrap();
 s.command(r#"{"op":"widget","id":1,"kind":"donut","width":2000000000,"height":1000000000,"alpha":0.75,"enabled":false,"selected":true,"data":[1,2,4]}"#).unwrap();
 let saved=s.snapshot().unwrap();let info=s.info();
 for property in [r#""width":2000000000"#,r#""height":1000000000"#,r#""alpha":0.75"#,r#""enabled":false"#,r#""selected":true"#]{assert!(info.contains(property),"missing {property}");}
 let data=|metadata:&str| -> Vec<f64>{
  let array=metadata.split_once("\"data\":[").expect("widget data").1.split_once(']').expect("data end").0;
  array.split(',').map(|number|number.parse::<f64>().expect("numeric widget sample")).collect()
 };
 assert_eq!(data(&info),vec![1.,2.,4.]);
 assert_eq!(s.snapshot().unwrap(),saved);s.restore(&saved).unwrap();assert_eq!(s.info(),info);
 s.command(r#"{"op":"widget","id":1,"data":[9]}"#).unwrap();assert_eq!(data(&info),vec![1.,2.,4.]);assert_eq!(data(&s.info()),vec![9.]);
}

#[test]
fn accessibility_binding_ownership_and_coercion_rejection() {
    let mut s=NativeScene::new(42).unwrap();
    s.command(r#"{"op":"define","path":"/motion","value":true,"binding":{"family":"accessibility","field":"reducedMotion"}}"#).unwrap();
    s.command(r#"{"op":"bind","path":"/motion","binding":{"family":"accessibility","field":"screenReader"}}"#).unwrap();
    s.command(r#"{"op":"set","path":"/motion","value":false}"#).unwrap();
    assert!(s.info().contains(r#""accessibility":{"reducedMotion":true,"screenReader":false}"#));
    let saved=s.snapshot().unwrap();
    assert!(s.command(r#"{"op":"set","path":"/motion","value":1}"#).is_err());
    assert_eq!(s.snapshot().unwrap(),saved);s.restore(&saved).unwrap();assert_eq!(s.snapshot().unwrap(),saved);
}

#[test]
fn explicit_region_state_and_indices_survive_restore() {
    let mut s=NativeScene::new(42).unwrap();let baseline=s.render().unwrap();let mut expected=baseline.bytes;
    let fg=u32::from_le_bytes(expected[4..8].try_into().unwrap())^0xffffff;expected[4..8].copy_from_slice(&fg.to_le_bytes());
    s.command(r#"{"op":"character-region","region":{"id":"fragment","path":"/app/fragment","state":"selected","cells":[0],"indices":[9]}}"#).unwrap();
    s.command(r#"{"op":"character-rule","rule":{"id":"fragment-paint","selector":{"path":"/app/fragment","indices":[9]},"states":{"selected":{"foregroundEffects":[{"type":"invert"}]}}}}"#).unwrap();
    assert!(s.inspectCharacterCell(0,0).is_err());
    let saved=s.snapshot().unwrap();assert_eq!(s.render().unwrap().bytes,expected);
    let inspected=s.inspectCharacterCell(0,0).unwrap();assert_eq!(inspected.path,"/app/fragment");assert_eq!(inspected.state,"selected");assert_eq!(inspected.index,9);
    assert_eq!(s.snapshot().unwrap(),saved);
    s.command(r#"{"op":"remove-character-region","id":"fragment"}"#).unwrap();s.restore(&saved).unwrap();
    assert!(s.inspectCharacterCell(0,0).is_err());
    assert_eq!(s.render().unwrap().bytes,expected);assert_eq!(s.snapshot().unwrap(),saved);assert_eq!(s.inspectCharacterCell(0,0).unwrap(),inspected);
}

#[test]
fn standalone_composite_spaces_have_independent_midpoints() {
    for (space,expected) in [0x808080,0xbcbcbc,0x636363,0x636363].into_iter().enumerate() {
        assert_eq!(NativeScene::compositeInSpace(0,0xffffff,65535,32768,0,0,0,space as u32).unwrap(),[expected,65535]);
        assert_eq!(NativeScene::compositeInSpace(0x123456,0xabcdef,65535,0,0,0,0,space as u32).unwrap(),[0x123456,65535]);
    }
    assert!(NativeScene::compositeInSpace(0,0,65535,65535,0,0,0,4).is_err());
}

#[test]
fn character_rules_match_independent_frame_oracle_and_restore() {
    let mut s=NativeScene::new(42).unwrap();let baseline=s.render().unwrap();
    let mut expected=baseline.bytes.clone();
    for x in 2..6 {
        let offset=(2*baseline.width as usize+x)*16+4;
        let foreground=u32::from_le_bytes(expected[offset..offset+4].try_into().unwrap())^0xffffff;
        expected[offset..offset+4].copy_from_slice(&foreground.to_le_bytes());
    }
    s.command(r#"{"op":"character-rule","rule":{"id":"invert","selector":{"rect":{"x":2,"y":2,"width":4,"height":1}},"compositeSpace":"srgb","foregroundEffects":[{"type":"invert"}]}}"#).unwrap();
    let saved=s.snapshot().unwrap();assert_eq!(s.render().unwrap().bytes,expected);
    assert_eq!(s.snapshot().unwrap(),saved);assert!(s.info().contains(r#""characterRules":[{"id":"invert""#));
    s.command(r#"{"op":"remove-character-rule","id":"invert"}"#).unwrap();
    assert_eq!(s.render().unwrap().bytes,baseline.bytes);
    s.restore(&saved).unwrap();assert_eq!(s.render().unwrap().bytes,expected);assert_eq!(s.snapshot().unwrap(),saved);
}

#[test]
fn retained_transforms_read_execution_state_and_replay() {
    let mut s=NativeScene::new(42).unwrap();
    for command in [
        r#"{"op":"define","path":"/go","value":0}"#,
        r#"{"op":"define","path":"/seconds","value":2}"#,
        r#"{"op":"define","path":"/milliseconds","value":0}"#,
        r#"{"op":"trigger","id":1,"source":"/go","target":"/milliseconds","debounceMs":500,"expression":{"convert":{"value":{"path":"/seconds"},"from":"seconds","to":"milliseconds"}}}"#,
        r#"{"op":"set","path":"/go","value":1}"#,
        r#"{"op":"set","path":"/seconds","value":3}"#,
    ] {s.command(command).unwrap();}
    let start=s.snapshot().unwrap();
    assert!(s.command(r#"{"op":"remove-value","path":"/seconds"}"#).is_err());
    assert_eq!(start,s.snapshot().unwrap());
    s.advanceTo(500_000).unwrap();
    assert!(s.info().contains(r#""/milliseconds":3000"#));
    let finish=s.snapshot().unwrap();s.render().unwrap();assert_eq!(finish,s.snapshot().unwrap());
    s.restore(&start).unwrap();s.advanceTo(500_000).unwrap();assert_eq!(finish,s.snapshot().unwrap());
}

#[test]
fn node_and_indicator_bindings_match_public_authoring() {
    for (base,field,value,expected) in [
        (r#"{"op":"node","id":1,"label":"SDK card","position":[0,6,0]}"#,
         "color",11189196,r#"{"op":"node","id":1,"color":11189196}"#),
        (r#"{"op":"indicator","id":1,"stepMs":120}"#,
         "stepMs",200,r#"{"op":"indicator","id":1,"stepMs":200}"#),
    ] {
        let mut s=NativeScene::new(42).unwrap();let mut oracle=NativeScene::new(42).unwrap();
        s.command(base).unwrap();oracle.command(base).unwrap();
        let family=if field=="color" {"node"} else {"indicator"};
        s.command(&format!(r#"{{"op":"define","path":"/control","value":{value},"binding":{{"family":"{family}","id":1,"field":"{field}"}}}}"#)).unwrap();
        s.command(r#"{"op":"remove-value","path":"/control"}"#).unwrap();oracle.command(expected).unwrap();
        assert_eq!(s.snapshot().unwrap(),oracle.snapshot().unwrap());
        s.advanceTo(1_000_000).unwrap();oracle.advanceTo(1_000_000).unwrap();
        assert_eq!(s.render().unwrap().bytes,oracle.render().unwrap().bytes);
    }
}

#[test]
fn typed_payload_copies_survive_acknowledgement_without_coercion() {
    let mut s=NativeScene::new(42).unwrap();
    for command in [
        r#"{"op":"define","path":"/task","type":"json","value":{}}"#,
        r#"{"op":"define","path":"/name","value":""}"#,
        r#"{"op":"define","path":"/ready","value":false}"#,
        r#"{"op":"emit-intent","event":"/host/task","payload":{"task":{"id":"noc-1","ready":true,"items":[1,null,false]}}}"#,
        r#"{"op":"set","path":"/task","intentId":1,"expression":{"intentPath":"/task"}}"#,
        r#"{"op":"set","path":"/name","intentId":1,"expression":{"intentPath":"/task/id"}}"#,
        r#"{"op":"set","path":"/ready","intentId":1,"expression":{"intentPath":"/task/ready"}}"#,
        r#"{"op":"ack-intent","id":1}"#,
    ] {s.command(command).unwrap();}
    let info=s.info();
    assert!(info.contains(r#""/task":{"id":"noc-1","ready":true,"items":[1,null,false]}"#));
    assert!(info.contains(r#""/name":"noc-1""#));assert!(info.contains(r#""/ready":true"#));assert!(info.contains(r#""intents":[]"#));
    let before=s.snapshot().unwrap();
    assert!(s.command(r#"{"op":"set","path":"/ready","value":1}"#).is_err());assert_eq!(before,s.snapshot().unwrap());
    s.render().unwrap();assert_eq!(before,s.snapshot().unwrap());s.restore(&before).unwrap();assert_eq!(before,s.snapshot().unwrap());
}

#[test]
fn retained_typed_guard_and_action_own_sources_and_replay() {
    let mut s=NativeScene::new(42).unwrap();
    for command in [
        r#"{"op":"define","path":"/title","value":""}"#,
        r#"{"op":"define","path":"/ready","value":true}"#,
        r#"{"op":"trigger","id":1,"target":"/title","event":"/host/task","debounceMs":500,"whenExpression":{"and":[{"path":"/ready"},{"equal":[{"intentPath":"/task/status"},"ready"]}]},"expression":{"concat":["Task: ",{"intentPath":"/task/title"}]}}"#,
        r#"{"op":"emit-intent","event":"/host/task","payload":{"task":{"status":"ready","title":"NOC 日本"}}}"#,
    ] {s.command(command).unwrap();}
    let start=s.snapshot().unwrap();assert!(s.command(r#"{"op":"remove-value","path":"/ready"}"#).is_err());assert_eq!(start,s.snapshot().unwrap());
    s.advanceTo(500_000).unwrap();let info=s.info();assert!(info.contains(r#""/title":"Task: NOC 日本""#));assert!(info.contains(r#""lastIntent":1"#));
    let finish=s.snapshot().unwrap();s.render().unwrap();assert_eq!(finish,s.snapshot().unwrap());
    s.restore(&start).unwrap();s.advanceTo(500_000).unwrap();assert_eq!(finish,s.snapshot().unwrap());
}

#[test]
fn computed_json_numbers_preserve_binary64_and_snapshot_import() {
    let mut s=NativeScene::new(42).unwrap();
    s.command(r#"{"op":"define","path":"/json","type":"json","value":0}"#).unwrap();
    s.command(r#"{"op":"set","path":"/json","expression":{"divide":[1,3]}}"#).unwrap();
    let saved=s.snapshot().unwrap();let offset=24+5958112+8+8+4096+24;
    let mut bytes=[0u8;8];bytes.copy_from_slice(&saved[offset..offset+8]);
    assert_eq!(u64::from_le_bytes(bytes),(1.0f64/3.0).to_bits());
    s.render().unwrap();assert_eq!(saved,s.snapshot().unwrap());s.restore(&saved).unwrap();assert_eq!(saved,s.snapshot().unwrap());
}

#[test]
fn surface_and_wave_bindings_match_public_edits() {
    for (define,edit) in [
        (r#"{"op":"define","path":"/control","value":11259375,"binding":{"family":"surface","id":1,"field":"heatColor"}}"#,
         r#"{"op":"surface","id":1,"heatColor":11259375}"#),
        (r#"{"op":"define","path":"/control","value":false,"binding":{"family":"surface","id":1,"field":"renderVisible"}}"#,
         r#"{"op":"surface","id":1,"renderVisible":false}"#),
        (r#"{"op":"define","path":"/control","value":0.75,"binding":{"family":"surface-wave","id":1,"field":"waves.0.amplitude"}}"#,
         r#"{"op":"surface-waves","surfaceId":1,"waves":[[0.75,0.2,0.3,2,0.4]]}"#),
    ] {
        let mut s=NativeScene::new(42).unwrap();let mut oracle=NativeScene::new(42).unwrap();
        for scene in [&mut s,&mut oracle] {
            scene.command(r#"{"op":"surface","id":1}"#).unwrap();
            scene.command(r#"{"op":"surface-waves","surfaceId":1,"waves":[[1,0.2,0.3,2,0.4]]}"#).unwrap();
        }
        s.command(define).unwrap();s.command(r#"{"op":"remove-value","path":"/control"}"#).unwrap();
        oracle.command(edit).unwrap();assert_eq!(s.snapshot().unwrap(),oracle.snapshot().unwrap());
    }
}

#[test]
fn ordered_payload_guard_retains_event_ownership() {
    let mut s=NativeScene::new(42).unwrap();
    for command in [
        r#"{"op":"define","path":"/out","value":0}"#,
        r#"{"op":"trigger","id":1,"target":"/out","event":"/host/metric","whenExpression":{"greaterOrEqual":[{"intentPath":"/metric"},3]},"value":7}"#,
        r#"{"op":"emit-intent","event":"/host/metric","payload":{"metric":4}}"#,
    ] {s.command(command).unwrap();}
    let info=s.info();assert!(info.contains(r#""/out":7"#));assert!(info.contains(r#""event":"/host/metric""#));
    let saved=s.snapshot().unwrap();s.render().unwrap();assert_eq!(saved,s.snapshot().unwrap());
}
