package native
import("math";"testing")
func TestAngularExchangeIndependentAxesAndEnergy(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close();i,j,k:=[3]float64{2,4,8},[3]float64{3,5,7},[3]float64{4,0,2};a,b:=[3]float64{5,-2,1},[3]float64{-1,3,0}
 row,e:=s.AngularDragExchange(i,j,k,.5,a,b);if e!=nil{t.Fatal(e)};lost:=0.0
 for axis:=0;axis<3;axis++{f:=-math.Expm1(-k[axis]*.5*(1/i[axis]+1/j[axis]));mu:=i[axis]*j[axis]/(i[axis]+j[axis]);impulse:=mu*f*(a[axis]-b[axis]);lost+=.5*mu*(a[axis]-b[axis])*(a[axis]-b[axis])*f*(2-f)
  if math.Abs(row[axis]-(a[axis]-impulse/i[axis]))>1e-9||math.Abs(row[axis+3]-(b[axis]+impulse/j[axis]))>1e-9{t.Fatal(row)}
  if math.Abs(i[axis]*row[axis]+j[axis]*row[axis+3]-(i[axis]*a[axis]+j[axis]*b[axis]))>1e-9{t.Fatal("angular momentum")}}
 if math.Abs(row[9]-lost)>1e-9{t.Fatal("rotational energy")};row[0]=999;fresh,e:=s.AngularDragExchange(i,j,k,.5,a,b);if e!=nil||fresh[0]==999{t.Fatal(fresh,e)}
 if _,e=s.AngularDragExchange([3]float64{2,4,0},j,k,.5,a,b);e==nil{t.Fatal("zero inertia accepted")}
}
func TestFiniteMassExchangeConservationPartitionOwnership(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 a,b:=[3]float64{5,-2,1},[3]float64{-1,3,0}
 row,e:=s.FluidDragExchange(2,3,4,.5,a,b);if e!=nil{t.Fatal(e)}
 f:=-math.Expm1(-4*.5*(1.0/2+1.0/3));lost:=0.0
 for i:=0;i<3;i++{relative:=a[i]-b[i];impulse:=1.2*f*relative;lost+=.6*relative*relative*f*(2-f)
  if math.Abs(row[i]-(a[i]-impulse/2))>1e-9||math.Abs(row[i+3]-(b[i]+impulse/3))>1e-9||math.Abs(row[i+6]-impulse)>1e-9{t.Fatal(row)}
  if math.Abs(2*row[i]+3*row[i+3]-(2*a[i]+3*b[i]))>1e-9{t.Fatal("momentum",row)}
 }
 if math.Abs(row[9]-lost)>1e-9{t.Fatal("energy",row)}
 second,e:=s.FluidDragExchange(2,3,4,.5,[3]float64{row[0],row[1],row[2]},[3]float64{row[3],row[4],row[5]});if e!=nil{t.Fatal(e)}
 full,e:=s.FluidDragExchange(2,3,4,1,a,b);if e!=nil{t.Fatal(e)}
 for i:=0;i<6;i++{if math.Abs(second[i]-full[i])>1e-9{t.Fatal("partition",second,full)}}
 if math.Abs(row[9]+second[9]-full[9])>1e-9{t.Fatal("partition energy")}
 row[0]=999;fresh,e:=s.FluidDragExchange(2,3,4,.5,a,b);if e!=nil||fresh[0]==999{t.Fatal("ownership",fresh,e)}
 if _,e=s.FluidDragExchange(0,3,4,.5,a,b);e==nil{t.Fatal("invalid mass accepted")}
}
