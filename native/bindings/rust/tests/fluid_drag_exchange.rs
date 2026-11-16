use nocturne_native::NativeScene;
#[test]
fn angular_exchange_independent_axes_and_energy(){
 let scene=NativeScene::new(2030).unwrap();let i=[2.0,4.0,8.0];let j=[3.0,5.0,7.0];let k=[4.0,0.0,2.0];let a=[5.0,-2.0,1.0];let b=[-1.0,3.0,0.0];
 let mut row=scene.angular_drag_exchange(i,j,k,0.5,a,b).unwrap();let mut lost=0.0;
 for axis in 0..3{let exponent:f64=-k[axis]*0.5*(1.0/i[axis]+1.0/j[axis]);let f=-exponent.exp_m1();let mu=i[axis]*j[axis]/(i[axis]+j[axis]);let impulse=mu*f*(a[axis]-b[axis]);lost+=0.5*mu*(a[axis]-b[axis]).powi(2)*f*(2.0-f);
 assert!((row[axis]-(a[axis]-impulse/i[axis])).abs()<1e-9);assert!((row[axis+3]-(b[axis]+impulse/j[axis])).abs()<1e-9);
 assert!((i[axis]*row[axis]+j[axis]*row[axis+3]-(i[axis]*a[axis]+j[axis]*b[axis])).abs()<1e-9);}
 assert!((row[9]-lost).abs()<1e-9);row[0]=999.0;assert_ne!(scene.angular_drag_exchange(i,j,k,0.5,a,b).unwrap()[0],999.0);
 assert!(scene.angular_drag_exchange([2.0,4.0,0.0],j,k,0.5,a,b).is_err());
}
#[test]
fn finite_mass_exchange_conservation_partition_and_ownership(){
 let scene=NativeScene::new(2030).unwrap();let a=[5.0,-2.0,1.0];let b=[-1.0,3.0,0.0];
 let mut row=scene.fluid_drag_exchange(2.0,3.0,4.0,0.5,a,b).unwrap();
 let f=-(-4.0_f64*0.5*(1.0/2.0+1.0/3.0)).exp_m1();let mut lost=0.0;
 for i in 0..3{let relative=a[i]-b[i];let impulse=1.2*f*relative;lost+=0.6*relative*relative*f*(2.0-f);
  assert!((row[i]-(a[i]-impulse/2.0)).abs()<1e-9);assert!((row[i+3]-(b[i]+impulse/3.0)).abs()<1e-9);assert!((row[i+6]-impulse).abs()<1e-9);
  assert!((2.0*row[i]+3.0*row[i+3]-(2.0*a[i]+3.0*b[i])).abs()<1e-9);
 }
 assert!((row[9]-lost).abs()<1e-9);
 let second=scene.fluid_drag_exchange(2.0,3.0,4.0,0.5,[row[0],row[1],row[2]],[row[3],row[4],row[5]]).unwrap();
 let full=scene.fluid_drag_exchange(2.0,3.0,4.0,1.0,a,b).unwrap();for i in 0..6{assert!((second[i]-full[i]).abs()<1e-9)}
 assert!((row[9]+second[9]-full[9]).abs()<1e-9);row[0]=999.0;assert_ne!(scene.fluid_drag_exchange(2.0,3.0,4.0,0.5,a,b).unwrap()[0],999.0);
 assert!(scene.fluid_drag_exchange(0.0,3.0,4.0,0.5,a,b).is_err());
}
