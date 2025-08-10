bl_info = {
    "name": "Mesh Isolate",
    "url":"https://cults3d.com/en/users/runictapestery47/3d-models",
    "author": "RunicTape",
    "version": (1, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Auto Hide",
    "description": "Hides visible objects in Edit Mode, restores them in Object Mode",
    "category": "3D View",
}

import bpy

# Store hidden objects
hidden_objects = set()
last_mode = None

def update_visibility():
    global hidden_objects, last_mode

    prefs = bpy.context.scene.auto_hide_settings
    if not prefs.enable_auto_hide:
        return

    current_mode = bpy.context.mode

    if current_mode == last_mode:
        return  # No change

    last_mode = current_mode
                
    if current_mode == 'EDIT_MESH':
        hidden_objects.clear()
        for obj in bpy.context.visible_objects:
            if (
                obj != bpy.context.active_object
                and obj.visible_get()
                and not getattr(obj, "auto_hide_exempt", False)
            ):
                obj.hide_viewport = True
                hidden_objects.add(obj.name)
            

    elif current_mode == 'OBJECT':
        for name in hidden_objects:
            obj = bpy.data.objects.get(name)
            if obj:
                obj.hide_viewport = False
        hidden_objects.clear()

class ModeWatcherOperator(bpy.types.Operator):
    """Watches for mode changes"""
    bl_idname = "wm.mode_watcher"
    bl_label = "Mode Watcher"

    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            update_visibility()
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class AutoHideSettings(bpy.types.PropertyGroup):
    enable_auto_hide: bpy.props.BoolProperty(
        name="Enable Auto Hide",
        description="Toggle automatic hiding of objects in Edit Mode",
        default=True
    )

class AutoHidePanel(bpy.types.Panel):
    bl_label = "Isolate Settings"
    bl_idname = "VIEW3D_PT_auto_hide"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Isolate'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.auto_hide_settings, "enable_auto_hide")
        layout.operator("object.bulk_exempt", icon='RESTRICT_VIEW_OFF')
        
class AutoHideObjectPanel(bpy.types.Panel):
    bl_label = "Auto Hide Settings"
    bl_idname = "OBJECT_PT_auto_hide"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj:
            layout.prop(obj, "auto_hide_exempt")
            
class BulkExemptOperator(bpy.types.Operator):
    """Toggle Auto Hide Exempt for selected objects"""
    bl_idname = "object.bulk_exempt"
    bl_label = "Toggle Exempt for Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        # Determine majority state to toggle consistently
        exempt_count = sum(1 for obj in selected if obj.auto_hide_exempt)
        target_state = exempt_count < len(selected) / 2

        for obj in selected:
            obj.auto_hide_exempt = target_state

        self.report({'INFO'}, f"Set exempt = {target_state} for {len(selected)} objects")
        return {'FINISHED'}


def start_mode_watcher(dummy):
    bpy.ops.wm.mode_watcher()

def register():
    bpy.utils.register_class(ModeWatcherOperator)
    bpy.utils.register_class(AutoHideSettings)
    bpy.utils.register_class(AutoHidePanel)
    bpy.utils.register_class(AutoHideObjectPanel)
    bpy.utils.register_class(BulkExemptOperator)
    bpy.types.Scene.auto_hide_settings = bpy.props.PointerProperty(type=AutoHideSettings)
    bpy.types.Object.auto_hide_exempt = bpy.props.BoolProperty(
    name="Auto Hide Exempt",
    description="Prevent this object from being hidden automatically",
    default=False
)


    # Start the operator after Blender loads
    bpy.app.timers.register(lambda: bpy.ops.wm.mode_watcher(), first_interval=1.0)

def unregister():
    bpy.utils.unregister_class(ModeWatcherOperator)
    bpy.utils.unregister_class(AutoHideSettings)
    bpy.utils.unregister_class(AutoHidePanel)
    bpy.utils.unregister_class(AutoHideObjectPanel)
    bpy.utils.unregister_class(BulkExemptOperator)
    del bpy.types.Object.auto_hide_exempt
    del bpy.types.Scene.auto_hide_settings