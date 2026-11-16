#![allow(non_snake_case,unused_mut)]
// Generated only by explicit fixture acceptance; generation never runs in CI.
use nocturne_surfaces::studio::{Studio,StageKey,Node,NodeKey,NodeKind,Impulse};
fn fnv(bytes:&[u8])->u64 {bytes.iter().fold(14695981039346656037u64,|h,b|(h^(*b as u64)).wrapping_mul(1099511628211))}
#[test] fn acceptedStudioFixtures(){
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,0).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1234,&nodes,&events).unwrap().toBytes()),0xfc9dc9eb81412609u64,"pattern-0-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,0).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1234,&nodes,&events).unwrap().toBytes()),0xa5321ac332a7c675u64,"pattern-0-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,0).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1234,&nodes,&events).unwrap().toBytes()),0xa026a61b7e7ed579u64,"pattern-0-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,0).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1234,&nodes,&events).unwrap().toBytes()),0x48068eef6c43878bu64,"pattern-0-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,1).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1307,&nodes,&events).unwrap().toBytes()),0x61f2b51a8fb57a60u64,"pattern-1-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,1).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1307,&nodes,&events).unwrap().toBytes()),0x9b601e71f3e731deu64,"pattern-1-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,1).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1307,&nodes,&events).unwrap().toBytes()),0x0f15861cd30afd2au64,"pattern-1-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,1).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1307,&nodes,&events).unwrap().toBytes()),0x8dbbb3c7f2b09832u64,"pattern-1-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,2).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1380,&nodes,&events).unwrap().toBytes()),0x680126c55bf4aa87u64,"pattern-2-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,2).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1380,&nodes,&events).unwrap().toBytes()),0x1a0a9ec5dd767110u64,"pattern-2-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,2).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1380,&nodes,&events).unwrap().toBytes()),0xcf23f6442b128c62u64,"pattern-2-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,2).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1380,&nodes,&events).unwrap().toBytes()),0x4084ebcc9e620fa7u64,"pattern-2-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,3).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1453,&nodes,&events).unwrap().toBytes()),0xb331154d6aac6fe2u64,"pattern-3-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,3).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1453,&nodes,&events).unwrap().toBytes()),0x6b7ce62b476ec411u64,"pattern-3-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,3).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1453,&nodes,&events).unwrap().toBytes()),0x6680411ba27a94c4u64,"pattern-3-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,3).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1453,&nodes,&events).unwrap().toBytes()),0x290a1c65edcc97d5u64,"pattern-3-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,4).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1526,&nodes,&events).unwrap().toBytes()),0xbf66a5f52cfc10f3u64,"pattern-4-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,4).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1526,&nodes,&events).unwrap().toBytes()),0x0001ae7c773fe908u64,"pattern-4-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,4).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1526,&nodes,&events).unwrap().toBytes()),0xefe5f3b3dff0e65au64,"pattern-4-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,4).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1526,&nodes,&events).unwrap().toBytes()),0xa27db9e033aba1c1u64,"pattern-4-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,5).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1599,&nodes,&events).unwrap().toBytes()),0xa5f290a0721815a8u64,"pattern-5-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,5).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1599,&nodes,&events).unwrap().toBytes()),0x59fa9976c83d95f9u64,"pattern-5-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,5).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1599,&nodes,&events).unwrap().toBytes()),0x728b97feba3316feu64,"pattern-5-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,5).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1599,&nodes,&events).unwrap().toBytes()),0xaff87b9205be111au64,"pattern-5-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,6).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1672,&nodes,&events).unwrap().toBytes()),0x168e31c7685b4a98u64,"pattern-6-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,6).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1672,&nodes,&events).unwrap().toBytes()),0xd2ffa8ac6e7fbb9eu64,"pattern-6-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,6).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1672,&nodes,&events).unwrap().toBytes()),0x4927a5a0e8aab788u64,"pattern-6-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,6).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1672,&nodes,&events).unwrap().toBytes()),0x1679ea1ce8a2949au64,"pattern-6-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,7).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1745,&nodes,&events).unwrap().toBytes()),0x7c718cbcdef178d6u64,"pattern-7-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,7).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1745,&nodes,&events).unwrap().toBytes()),0xe458a901995ee862u64,"pattern-7-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,7).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1745,&nodes,&events).unwrap().toBytes()),0x5467a894ea3aa94du64,"pattern-7-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,7).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1745,&nodes,&events).unwrap().toBytes()),0xef62d12ea449ba02u64,"pattern-7-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,8).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1818,&nodes,&events).unwrap().toBytes()),0xd68633f4181f2d0au64,"pattern-8-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,8).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1818,&nodes,&events).unwrap().toBytes()),0x3fcca3bc152092eau64,"pattern-8-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,8).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1818,&nodes,&events).unwrap().toBytes()),0x298a6baa2dde84e3u64,"pattern-8-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,8).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1818,&nodes,&events).unwrap().toBytes()),0x95c6526b6bb5f956u64,"pattern-8-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,9).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1891,&nodes,&events).unwrap().toBytes()),0xc9a926d5eb0ab42cu64,"pattern-9-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,9).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1891,&nodes,&events).unwrap().toBytes()),0xbf774d540c3cd7cfu64,"pattern-9-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,9).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1891,&nodes,&events).unwrap().toBytes()),0xa61e6a8ee6b02c06u64,"pattern-9-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,9).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1891,&nodes,&events).unwrap().toBytes()),0x17d59ad23054a3eeu64,"pattern-9-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,10).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1964,&nodes,&events).unwrap().toBytes()),0x220927fa7aed4155u64,"pattern-10-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,10).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1964,&nodes,&events).unwrap().toBytes()),0x87e971e89eb3008cu64,"pattern-10-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,10).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1964,&nodes,&events).unwrap().toBytes()),0xfb67881d04ecb32bu64,"pattern-10-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,10).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1964,&nodes,&events).unwrap().toBytes()),0x2cc31e5e63ad1111u64,"pattern-10-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,11).unwrap();
s.set(StageKey::PixelMode,0).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(2037,&nodes,&events).unwrap().toBytes()),0xb6c33cb104f87071u64,"pattern-11-pixel-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,11).unwrap();
s.set(StageKey::PixelMode,1).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(2037,&nodes,&events).unwrap().toBytes()),0xb5a3181a11052766u64,"pattern-11-pixel-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,11).unwrap();
s.set(StageKey::PixelMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(2037,&nodes,&events).unwrap().toBytes()),0xef169555f56636aeu64,"pattern-11-pixel-2");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Pattern,11).unwrap();
s.set(StageKey::PixelMode,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(2037,&nodes,&events).unwrap().toBytes()),0x5a1c7dde6fa3b819u64,"pattern-11-pixel-3");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Text,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x5fe9a2307a4a2c8eu64,"node-text");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Box,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0xadc04bac301a9702u64,"node-box");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Rule,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x767ca763ddddc5cdu64,"node-rule");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Button,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0xc43ec59b2a33cb11u64,"node-button");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Item,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x479f41fc790aff76u64,"node-item");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Cursor,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x0fc23a8e7d9310e1u64,"node-cursor");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Progress,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x21c4318cd3e4db55u64,"node-progress");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Bars,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x69116bde8fda595cu64,"node-bars");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Pie,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x931edf5cafc9d5edu64,"node-pie");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Donut,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0xfca082faa02067dbu64,"node-donut");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Scatter,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x70068cf21e22082du64,"node-scatter");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Line,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x48224983b8b06f0fu64,"node-line");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Digits,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x6550304eba65ab04u64,"node-digits");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut n=Node::new(NodeKind::Edge,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);
let mut events=Vec::new();
assert_eq!(fnv(&s.render(5432,&nodes,&events).unwrap().toBytes()),0x70eddfe44b93e8fcu64,"node-edge");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
events.push(Impulse{xQ8:5120,yQ8:2304,strength:1000,kind:0,atMs:6000,id:15});
assert_eq!(fnv(&s.render(7000,&nodes,&events).unwrap().toBytes()),0xa014921289f15232u64,"impulse-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,40).unwrap();
s.set(StageKey::Height,18).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
events.push(Impulse{xQ8:5120,yQ8:2304,strength:1000,kind:1,atMs:6000,id:15});
assert_eq!(fnv(&s.render(7000,&nodes,&events).unwrap().toBytes()),0xa240a87b9fa5f79cu64,"impulse-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::FocusMode,0).unwrap();
s.set(StageKey::FocusX,2560).unwrap();
s.set(StageKey::FocusY,1536).unwrap();
s.set(StageKey::Pattern,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1000000000000,&nodes,&events).unwrap().toBytes()),0xeb91524fdd5c1f8au64,"focus-0-long-clock");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::FocusMode,1).unwrap();
s.set(StageKey::FocusX,2560).unwrap();
s.set(StageKey::FocusY,1536).unwrap();
s.set(StageKey::Pattern,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1000000000000,&nodes,&events).unwrap().toBytes()),0x63024a67b7444bf2u64,"focus-1-long-clock");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::FocusMode,2).unwrap();
s.set(StageKey::FocusX,2560).unwrap();
s.set(StageKey::FocusY,1536).unwrap();
s.set(StageKey::Pattern,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1000000000000,&nodes,&events).unwrap().toBytes()),0xb13ef2420f710adcu64,"focus-2-long-clock");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::FocusMode,3).unwrap();
s.set(StageKey::FocusX,2560).unwrap();
s.set(StageKey::FocusY,1536).unwrap();
s.set(StageKey::Pattern,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1000000000000,&nodes,&events).unwrap().toBytes()),0x879d6e46b58f6ff1u64,"focus-3-long-clock");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::FocusMode,4).unwrap();
s.set(StageKey::FocusX,2560).unwrap();
s.set(StageKey::FocusY,1536).unwrap();
s.set(StageKey::Pattern,3).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(1000000000000,&nodes,&events).unwrap().toBytes()),0xbc98a16aa249c4b3u64,"focus-4-long-clock");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Quantize,0).unwrap();
s.set(StageKey::Pattern,4).unwrap();
s.set(StageKey::PivotX,-70000).unwrap();
s.set(StageKey::PivotY,42000).unwrap();
s.set(StageKey::RotationMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(4294969999,&nodes,&events).unwrap().toBytes()),0x5cf43487433ae004u64,"quantize-0");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Quantize,1).unwrap();
s.set(StageKey::Pattern,4).unwrap();
s.set(StageKey::PivotX,-70000).unwrap();
s.set(StageKey::PivotY,42000).unwrap();
s.set(StageKey::RotationMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(4294969999,&nodes,&events).unwrap().toBytes()),0xfc5cd39534d5ce9cu64,"quantize-1");}
{let mut s=Studio::new().unwrap();
s.set(StageKey::Width,31).unwrap();
s.set(StageKey::Height,13).unwrap();
s.set(StageKey::Quantize,2).unwrap();
s.set(StageKey::Pattern,4).unwrap();
s.set(StageKey::PivotX,-70000).unwrap();
s.set(StageKey::PivotY,42000).unwrap();
s.set(StageKey::RotationMode,2).unwrap();
let mut nodes=Vec::new();
let mut events=Vec::new();
assert_eq!(fnv(&s.render(4294969999,&nodes,&events).unwrap().toBytes()),0xa31ea65e834fee01u64,"quantize-2");}
}
