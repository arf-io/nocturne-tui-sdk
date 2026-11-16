package main
import ("fmt"; "os"; nocturne "nocturne/native")
func run() error {
 scene,err:=nocturne.New(2030);if err!=nil{return err};defer scene.Close()
 commands,err:=os.ReadFile("../panel.json");if err!=nil{return err}
 if _,err=scene.CommandRaw(commands);err!=nil{return err}
 if err=scene.AdvanceTo(500000);err!=nil{return err}
 frame,err:=scene.Render();if err!=nil{return err}
 checkpoint,err:=scene.Snapshot();if err!=nil{return err}
 if err=scene.Restore(checkpoint);err!=nil{return err}
 fmt.Println(frame.Width,frame.Height,len(frame.Bytes));return nil
}
func main(){if err:=run();err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)}}
