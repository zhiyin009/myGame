#![allow(dead_code, unused_imports)]

use std::{
    any::Any,
    borrow::Borrow,
    default,
    ops::DerefMut,
    ptr::{self, null, null_mut},
    vec,
};

use bevy::{
    asset::Asset,
    ecs::{bundle::Bundles, entity},
    input::mouse::{MouseButtonInput, MouseMotion, MouseWheel},
    prelude::*,
    reflect::TypeUuid,
    render::{
        mesh::MeshPlugin,
        render_resource::{AsBindGroup, ShaderRef},
    },
    sprite::*,
};
use bevy_mod_picking::*;
use rand::prelude::*;
use rand::seq::SliceRandom;

const GRID_COLOR: &[Color] = &[Color::BLUE, Color::PURPLE, Color::GOLD];
const GRID_SIZE_X: f32 = 20.0;
const GRID_SIZE_Y: f32 = 20.0;
const WIDTH: f32 = 720.0;
const HEIGHT: f32 = 720.0;

#[derive(Component, PartialEq, Debug)]
struct Grid {
    color: Color,
}
#[derive(Default, Deref, DerefMut)]
struct LinkedGrids(Vec<Entity>);

struct GameOverEvent;

fn main() {
    let window = WindowDescriptor {
        title: "连连看".to_string(),
        width: WIDTH,
        height: HEIGHT,
        // resizable: true,
        ..default()
    };

    App::new()
        .insert_resource(window)
        .add_startup_system(spawn_grid)
        .insert_resource(ClearColor(Color::WHITE))
        .insert_resource(LinkedGrids::default())
        .add_startup_system(setup)
        .add_system(grid_events)
        .add_event::<GameOverEvent>()
        .add_system(link_grid.after(grid_events))
        .add_system(game_over.after(link_grid))
        .add_plugins(DefaultPlugins)
        .add_plugins(DefaultPickingPlugins)
        .add_system_to_stage(CoreStage::PostUpdate, grid_events)
        .run();
}

fn setup(mut commands: Commands) {
    commands
        .spawn_bundle(Camera2dBundle::default())
        .insert_bundle(PickingCameraBundle::default());
}

fn spawn_grid(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<ColorMaterial>>,
) {
    for _ in 1..=5 {
        let color = GRID_COLOR.choose(&mut rand::thread_rng()).unwrap();
        for _ in 0..2 {
            commands
                .spawn_bundle(MaterialMesh2dBundle {
                    mesh: meshes.add(Mesh::from(shape::Quad::default())).into(),
                    material: materials.add(ColorMaterial {
                        color: *color,
                        ..default()
                    }),
                    transform: Transform {
                        scale: Vec3 {
                            x: GRID_SIZE_X,
                            y: GRID_SIZE_Y,
                            z: 1.0,
                        },
                        translation: Vec3 {
                            x: rand::thread_rng().gen_range(-WIDTH / 2.0..WIDTH / 2.0),
                            y: rand::thread_rng().gen_range(-HEIGHT / 2.0..HEIGHT / 2.0),
                            z: 10.0,
                        },
                        ..default()
                    },
                    ..default()
                })
                .insert(Grid { color: *color })
                .insert_bundle(PickableBundle::default());
        }
    }
}

fn focus(transform: &mut Transform) {
    transform.scale = Vec3::new(GRID_SIZE_X * 1.2, GRID_SIZE_Y * 1.2, transform.scale.z);
}
fn defocus(transform: &mut Transform) {
    transform.scale = Vec3::new(GRID_SIZE_X, GRID_SIZE_Y, transform.scale.z)
}

fn grid_events(
    mut events: EventReader<PickingEvent>,
    mut all_grids: Query<(Entity, &Grid, &mut Transform, &Handle<ColorMaterial>), With<Grid>>,
    mut selected: Query<(Entity, &Grid, &mut Selection, &Handle<ColorMaterial>), With<NoDeselect>>,
    mut commands: Commands,
    mut linked_grids: ResMut<LinkedGrids>,
) {
    for event in events.iter() {
        match event {
            PickingEvent::Selection(e) => match e {
                SelectionEvent::JustDeselected(e) => {
                    if let Some((entity, _, mut transform, _)) = all_grids.get_mut(*e).ok() {
                        defocus(&mut transform);
                        commands.entity(entity).remove::<NoDeselect>();
                        info!("deselect {:?} {:?}", e, selected.iter().len());
                    }
                }
                SelectionEvent::JustSelected(e) => {
                    if let Some((entity, grid, mut transform, handle)) = all_grids.get_mut(*e).ok()
                    {
                        info!("select {:?}", entity);
                        focus(&mut transform);

                        commands.entity(entity).insert(NoDeselect);
                        for (selected_entity, selected_grid, mut selection, selected_handle) in
                            selected
                                .iter_mut()
                                .filter(|(e, _, _, _)| e.id() != entity.id())
                        {
                            if *selected_grid == *grid {
                                linked_grids.push(selected_entity);
                                linked_grids.push(entity);
                            } else {
                                info!("diff color");
                                commands.entity(selected_entity).remove::<NoDeselect>();
                                selection.set_selected(false);
                            }
                        }
                    }
                }
            },
            PickingEvent::Hover(e) => match e {
                HoverEvent::JustEntered(e) => {
                    if let Some((_, _, mut transform, _)) = all_grids.get_mut(*e).ok() {
                        focus(&mut transform);
                    }
                }
                HoverEvent::JustLeft(e) => {
                    if selected.get(*e).is_err() {
                        info!("get entity {:?}", *e);
                        if let Some((_, _, mut transform, _)) = all_grids.get_mut(*e).ok() {
                            defocus(&mut transform);
                        }
                    }
                }
            },
            PickingEvent::Clicked(_e) => {}
        }
    }
}

fn link_grid(
    mut commands: Commands,
    mut gameover_writer: EventWriter<GameOverEvent>,
    mut linked_grids: ResMut<LinkedGrids>,
    all_grids: Query<Entity, With<Grid>>,
) {
    for &linked in linked_grids.iter() {
        commands.entity(linked).despawn_recursive();
    }
    linked_grids.clear();

    info!("left {:?}", all_grids.iter().len());
    if all_grids.iter().len() == 0 {
        info!("game over {:?}", all_grids.iter().len());
        gameover_writer.send(GameOverEvent);
    }
}

fn game_over(
    commands: Commands,
    meshes: ResMut<Assets<Mesh>>,
    materials: ResMut<Assets<ColorMaterial>>,
    mut reader: EventReader<GameOverEvent>,
) {
    if reader.iter().next().is_some() {
        spawn_grid(commands, meshes, materials);
    }
}
