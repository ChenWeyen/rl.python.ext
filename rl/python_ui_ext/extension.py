# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.ext
import omni.ui as ui
import omni.kit.app
import omni.kit.raycast.query
import omni.usd
import omni.kit.actions.core
import omni.kit.menu.utils
import omni.appwindow

import carb
import carb.input


def _run_on_next_post_update(callback):
    """Schedule a one-shot callback to run on the next post-update (main thread)."""
    sub = [None]

    def on_post_update(_e):
        try:
            callback()
        finally:
            sub.clear()  # Unsubscribe

    sub[0] = omni.kit.app.get_app().get_post_update_event_stream().create_subscription_to_pop(
        on_post_update, name="rl.python_ui_ext.run_on_next_post_update"
    )


def run_ray_mesh_intersection(on_result=None):
    """Run a ray-mesh intersection test against the current USD stage mesh data.

    Args:
        on_result: Optional callable(str). Called with the result text when the
            raycast completes. If None, result is logged via carb.
    """
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        text = "No USD stage open"
        if on_result:
            _run_on_next_post_update(lambda: on_result(text))
        else:
            carb.log_warn(f"[rl.python_ui_ext] {text}")
        return

    y_up = True
    origin = (0.0, 0.0, 500.0)
    direction = (0.0, 0.0, -1.0)
    if y_up:
        origin = (0.0, 500.0, 0.0)
        direction = (0.0, -1.0, 0.0)

    ray = omni.kit.raycast.query.Ray(origin, direction)

    def on_raycast_result(_, result):
        if result.valid:
            path = result.get_target_usd_path() or "(no path)"
            pos = result.hit_position
            text = f"Hit {path} at ({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})"
        else:
            text = "Ray-mesh: no hit"

        if on_result:
            carb.log_info(f"[rl.python_ui_ext] {text}")
            _run_on_next_post_update(lambda: on_result(text))
        else:
            carb.log_info(f"[rl.python_ui_ext] {text}")

    raycast = omni.kit.raycast.query.acquire_raycast_query_interface()
    raycast.submit_raycast_query(ray, on_raycast_result)


# Functions and vars are available to other extensions as usual in python:
# `rl.python_ui_ext.some_public_function(x)`
def some_public_function(x: int):
    """This is a public function that can be called from other extensions."""
    print(f"[rl.python_ui_ext] some_public_function was called with {x}")
    return x ** x


# Any class derived from `omni.ext.IExt` in the top level module (defined in
# `python.modules` of `extension.toml`) will be instantiated when the extension
# gets enabled, and `on_startup(ext_id)` will be called. Later when the
# extension gets disabled on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    """This extension manages a simple counter UI."""
    # ext_id is the current extension id. It can be used with the extension
    # manager to query additional information, like where this extension is
    # located on the filesystem.
    def on_startup(self, _ext_id):
        """This is called every time the extension is activated."""
        print("[rl.python_ui_ext] Extension startup")

        self._count = 0
        self._key_label = None
        self._input = None
        self._keyboard = None
        self._keyboard_sub_id = None
        self._window = ui.Window(
            "RL Python UI Extension", width=300, height=300
        )

        # Register an action for ray-mesh intersection (callable from menu)
        action_registry = omni.kit.actions.core.get_action_registry()
        action_registry.register_action(
            _ext_id,
            "run_ray_mesh_intersection",
            self._on_run_ray_mesh_intersection,
            display_name="Run Ray-Mesh Intersection",
            description="Run ray-mesh intersection test against USD stage",
        )

        # Add item to Tools menu
        omni.kit.menu.utils.add_menu_items(
            [
                omni.kit.menu.utils.MenuItemDescription(
                    name="RL",
                    sub_menu=[
                        omni.kit.menu.utils.MenuItemDescription(
                            name="Run Ray-Mesh Intersection",
                            onclick_action=(_ext_id, "run_ray_mesh_intersection"),
                        )
                    ],
                )
            ],
            "Tools",
        )


        with self._window.frame:
            with ui.VStack():
                self._key_label = ui.Label("Press any key...")
                label = ui.Label("")

                def on_click():
                    self._count += 1
                    run_ray_mesh_intersection(on_result=lambda text: setattr(label, "text", text))

                def on_reset():
                    self._count = 0
                    label.text = "empty"

                on_reset()

                with ui.HStack():
                    ui.Button("raycast V3", clicked_fn=on_click)
                    ui.Button("Reset", clicked_fn=on_reset)

        self._subscribe_keyboard_events()

    def _subscribe_keyboard_events(self):
        """Subscribe to global keyboard events and print them to the UI."""
        try:
            app_window = omni.appwindow.get_default_app_window()
            if not app_window:
                carb.log_warn("[rl.python_ui_ext] No app window; cannot subscribe keyboard events")
                return

            self._keyboard = app_window.get_keyboard()
            if not self._keyboard:
                carb.log_warn("[rl.python_ui_ext] No keyboard device; cannot subscribe keyboard events")
                return

            self._input = carb.input.acquire_input_interface()
            self._keyboard_sub_id = self._input.subscribe_to_keyboard_events(self._keyboard, self._on_keyboard_event)
            carb.log_info("[rl.python_ui_ext] Subscribed to keyboard events")
        except Exception:
            carb.log_exception("[rl.python_ui_ext] Failed to subscribe to keyboard events")

    def _on_keyboard_event(self, e):
        # Keep the formatting defensive: different Kit versions expose slightly different fields.
        event_type = getattr(e, "type", None)
        key_input = getattr(e, "input", None)
        modifiers = getattr(e, "modifiers", None)
        msg = f"Key event: type={event_type} input={key_input} modifiers={modifiers}"
        carb.log_info(f"[rl.python_ui_ext] {msg}")

        if self._key_label is not None:
            _run_on_next_post_update(lambda: setattr(self._key_label, "text", msg))

    def _on_run_ray_mesh_intersection(self, *_args, **_kwargs):
        """Menu action: run ray-mesh intersection (no UI callback; result logged)."""
        run_ray_mesh_intersection()

    def on_shutdown(self):
        """This is called every time the extension is deactivated. It is used
        to clean up the extension state."""
        try:
            if self._input is not None and self._keyboard is not None and self._keyboard_sub_id is not None:
                self._input.unsubscribe_to_keyboard_events(self._keyboard, self._keyboard_sub_id)
                self._keyboard_sub_id = None
                carb.log_info("[rl.python_ui_ext] Unsubscribed from keyboard events")
        except Exception:
            carb.log_exception("[rl.python_ui_ext] Failed to unsubscribe keyboard events")
        print("[rl.python_ui_ext] Extension shutdown")
