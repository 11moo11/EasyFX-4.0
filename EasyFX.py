bl_info = {
    "name": "EasyFX",
    "description": "Do post-production in the Image Editor",
    "author": "Nils Soderman (rymdnisse) & DoubleZ (2.8 port)",
    "version": (1, 1, 1),
    "blender": (4, 0, 0),
    "location": "Image Editor > Sidebar (N)",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Render"
}

import bpy, math

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Operator,
                       AddonPreferences,
                       PropertyGroup,
                       )

from bpy.utils import register_class, unregister_class

# ------------------------------------------------------------------------
#    variables
# ------------------------------------------------------------------------

s_sky = False
s_cell = True
first = True
imgs = ""
skyimg = ""

def Auto_Update(self, context):
    if context.scene.easyfx.use_auto_update:
        bpy.ops.object.update_operator()

# ------------------------------------------------------------------------
#    store properties
# ------------------------------------------------------------------------

class MySettings(PropertyGroup):

    # Nodes
    use_auto_update: BoolProperty(
        name="Auto Update",
        description="Automatically update when a value is altered",
        default=True, update=Auto_Update)
    # Filters
    use_vignette: BoolProperty(
        name="Vignette",
        description="Gradual decrease in light intensity towards the image borders",
        default=False, update=Auto_Update)
    vignette_v: FloatProperty(name="Vignette Amount", description="Amount", default=70, min=0, max=100, subtype="PERCENTAGE", update=Auto_Update)
    use_glow: BoolProperty(
        name="Glow",
        description="Glow",
        default=False, update=Auto_Update)
    glow_em: BoolProperty(
        name="Only Emission",
        description="Only materials with an emission value will glow",
        default=False, update=Auto_Update)
    glow_v: FloatProperty(name="Glow Amount", description="Amount", default=1, min=0, update=Auto_Update)
    use_streaks: BoolProperty(
        name="Streaks",
        description="Streaks",
        default=False, update=Auto_Update)
    streaks_em: BoolProperty(
        name="Only Emission",
        description="Only materials with an emission value will generate streaks",
        default=False, update=Auto_Update)
    streaks_v: FloatProperty(name="Streak Amount", description="Amount", default=1, min=0, update=Auto_Update)
    streaks_n: IntProperty(name="Number of streaks", description="Number of streaks", default=4, min=2, max=16, update=Auto_Update)
    streaks_d: FloatProperty(name="Angle Offset", description="Streak angle offset", default=0, min=0, max=math.pi, unit='ROTATION', update=Auto_Update)
    sharpen_v: FloatProperty(name="Sharpen", description="Sharpen image", default=0, min=0, update=Auto_Update)
    soften_v: FloatProperty(name="Soften", description="Soften image", default=0, min=0, update=Auto_Update)
    
    # Blurs
    use_speedb: BoolProperty(
        name="Motion Blur",
        description="Blurs out fast motions",
        default=False, update=Auto_Update)
    motionb_v: FloatProperty(name="Motion blur amount", description="Amount of motion blur", default=1.0, min=0, update=Auto_Update)
    use_dof: BoolProperty(
        name="Depth of field",
        description="Range of distance that appears acceptably sharp",
        default=False, update=Auto_Update)
    dof_v: FloatProperty(name="Defocus amount", description="Amount of blur", default=50.0, min=0, max=128, update=Auto_Update)
    
    # Color
    bw_v: FloatProperty(name="Saturation", description="Saturation", default=1, min=0, max=4, subtype="FACTOR", update=Auto_Update)
    contrast_v: FloatProperty(name="Contrast", description="The difference in color and light between parts of an image", default=0, update=Auto_Update)
    brightness_v: FloatProperty(name="Brightness", description="Brightness", default=0, update=Auto_Update)
    shadows_v: FloatVectorProperty(name="Shadows", description="Shadows", subtype="COLOR_GAMMA", default=(1,1,1), min=0, max=2, update=Auto_Update)
    midtones_v: FloatVectorProperty(name="Midtones", description="Midtones", subtype="COLOR_GAMMA", default=(1,1,1), min=0, max=2, update=Auto_Update)
    highlights_v: FloatVectorProperty(name="Highlights", description="Highlights", subtype="COLOR_GAMMA", default=(1,1,1), min=0, max=2, update=Auto_Update)
    check_v: FloatVectorProperty(default=(1,1,1), subtype="COLOR_GAMMA", update=Auto_Update)
    
    # Distort / Lens
    use_flip: BoolProperty(
        name="Flip image",
        description="Flip image on the X axis",
        default=False, update=Auto_Update)
    lens_distort_v: FloatProperty(name="Distort", description="Distort the lens", default=0, min=-0.999, max=1, update=Auto_Update)
    dispersion_v: FloatProperty(name="Dispersion", description="A type of distortion in which there is a failure of a lens to focus all colors to the same convergence point", default=0, min=0, max=1, update=Auto_Update)
    use_flare: BoolProperty(
        name="Lens Flare",
        description="Lens Flare",
        default=False, update=Auto_Update)
    flare_type: EnumProperty(items=[('Fixed', 'Fixed', 'Fixed position'), ('Tracked', 'Tracked', 'Select if you want object to place in the viewport to act like the flare')], update=Auto_Update)
    flare_c: FloatVectorProperty(name="Highlights", description="Flare Color", subtype="COLOR_GAMMA", size=4, default=(1,0.3,0.084, 1), min=0, max=1, update=Auto_Update)    
    flare_x: FloatProperty(name="Flare X Pos", description="Flare X offset", default=0, update=Auto_Update)
    flare_y: FloatProperty(name="Flare Y Pos", description="Flare Y offset", default=0, update=Auto_Update)
    flare_streak_intensity: FloatProperty(name="Size", description="Streak Intensity", default=0.002, min=0, max=1, subtype='FACTOR', update=Auto_Update)
    flare_streak_lenght: FloatProperty(name="Size", description="Streak Length", default=1, max=3, min=0.001, subtype='FACTOR', update=Auto_Update)
    flare_streak_angle: FloatProperty(name="Size", description="Streak Rotation", default=0, max=math.pi, min=0, subtype='ANGLE', update=Auto_Update)
    flare_streak_streaks: IntProperty(name="Size", description="Streak Streaks", default=12, max=16, min=2, update=Auto_Update)
    flare_glow: FloatProperty(name="Size", description="Glow Intensity", default=0.03, min=0, max=1, subtype='FACTOR', update=Auto_Update)
    flare_ghost: FloatProperty(name="Size", description="Ghost Intensity", default=1, min=0, update=Auto_Update)
    flare_layer: BoolVectorProperty(name="test", subtype="LAYER", size=20, update=Auto_Update, default=(False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False))
    flaret_streak_intensity: FloatProperty(name="Size", description="Streak Intensity", default=0.03, min=0, max=1, subtype='FACTOR', update=Auto_Update)
    flaret_streak_lenght: FloatProperty(name="Size", description="Streak Length", default=1.5, max=3, min=0.001, subtype='FACTOR', update=Auto_Update)
    flaret_streak_angle: FloatProperty(name="Size", description="Streak Rotation", default=0, max=math.pi, min=0, subtype='ANGLE', update=Auto_Update)
    flaret_streak_streaks: IntProperty(name="Size", description="Streak Streaks", default=12, max=16, min=2, update=Auto_Update)
    flaret_glow: FloatProperty(name="Size", description="Glow Intensity", default=0.1, min=0, max=1, subtype='FACTOR', update=Auto_Update)
    flaret_ghost: FloatProperty(name="Size", description="Ghost Intensity", default=1.5, min=0, update=Auto_Update)
    flare_center_size: FloatProperty(name="Size", description="Size of the flare source", default=20, min=1, update=Auto_Update)
    
    # World
    use_mist: BoolProperty(
        name="Use Mist",
        description="Mist",
        default=False, update=Auto_Update)
    mist_sky: BoolProperty(
        name="Use Mist",
        description="The mist will affect the sky",
        default=True, update=Auto_Update)
    mist_offset: FloatProperty(name="Size", description="Offset", default=0, update=Auto_Update)
    mist_size: FloatProperty(name="Size", description="Amount", default=0.01, update=Auto_Update)
    mist_min: FloatProperty(name="Size", description="Minimum", default=0, min=0, max=1, update=Auto_Update, subtype="FACTOR")
    mist_max: FloatProperty(name="Size", description="Maximum", default=1, min=0, max=1, update=Auto_Update, subtype="FACTOR")
    mist_color: FloatVectorProperty(name="Mist Color", description="Mist Color", subtype="COLOR_GAMMA", size=4, default=(1,1,1,1), min=0, max=1, update=Auto_Update)
        
    # Settings
    use_cinematic_border: BoolProperty(
        name="Cinematic Border",
        description="Add black borders at top and bottom",
        default=False, update=Auto_Update)
    cinematic_border_v: FloatProperty(name="Cinematic Border", description="border height", default=0.4, min=0, max=1, update=Auto_Update)
    use_transparent_sky: BoolProperty(
        name="Transparent Sky",
        description="Render the sky as transparent",
        default=False, update=Auto_Update)
    use_cel_shading: BoolProperty(
        name="Cell Shading",
        description="Adds a black outline, mimic the style of a comic book or cartoon",
        default=False, update=Auto_Update)
    cel_thickness: FloatProperty(name="Cel shading thickness", description="Line thickness", default=1, min=0, subtype='PIXEL', update=Auto_Update)
    split_image: BoolProperty(
        name="Split Original",
        description="Split the image with the original render",
        default=False, update=Auto_Update)
    split_v: IntProperty(name="Split Value", description="Where to split the image", default=50, min=0, max=100, subtype='PERCENTAGE', update=Auto_Update)
    use_image_sky: BoolProperty(
        name="Image Sky",
        description="Use external image as sky",
        default=False, update=Auto_Update)
    image_sky_img: StringProperty(name="Sky Image", description="Image", default="", subtype='FILE_PATH', update=Auto_Update)
    image_sky_x: FloatProperty(name="Image Sky X", description="Image offset on the X axis", default=0, update=Auto_Update)
    image_sky_y: FloatProperty(name="Image Sky Y", description="Image offset on the Y axis", default=0, update=Auto_Update)
    image_sky_angle: FloatProperty(name="Image Sky Angle", description="Image Rotation", default=0, update=Auto_Update)
    image_sky_scale: FloatProperty(name="Image sky Scale", description="Image Scale", default=1, update=Auto_Update)
    layer_index: IntProperty(name="Layer Index", description="Render Layer to use as main", default=0, min=0, update=Auto_Update)

# ------------------------------------------------------------------------
#    Panels
# ------------------------------------------------------------------------
class EASYFX_PT_UpdatePanel(bpy.types.Panel):
    bl_category = "EasyFX"
    bl_label = "Update"
    bl_idname = "EASYFX_PT_Update"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator('object.update_render_operator', text="Update & re-Render", icon="RENDER_STILL")
        row = col.row(align=True)
        row.operator('object.update_operator', text="Update", icon="SEQ_CHROMA_SCOPE")
        scn = context.scene
        mytool = scn.easyfx
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(mytool, "use_auto_update", text="Auto Update")
        row.prop(mytool, "use_flip", text="Flip image")
        layout.prop(mytool, "split_image", text="Split with original")
        if mytool.split_image:
            layout.prop(mytool, "split_v", text="Split at")
        
class EASYFX_PT_FilterPanel(Panel):
    bl_category = "EasyFX"
    bl_label = "Filter"
    bl_idname = "EASYFX_PT_Filter"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = context.scene
        mytool = scn.easyfx
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(mytool, "use_glow", text="Glow")
        if mytool.use_glow:
            row = col.row(align=True)
            row.prop(mytool, "glow_em", text="Emission only (Cycles only)")
            row = col.row(align=True)
            row.prop(mytool, "glow_v", text="Threshold")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(mytool, "use_streaks", text="Streaks")
        if mytool.use_streaks:
            row = col.row(align=True)
            row.prop(mytool, "streaks_em", text="Emission only (Cycles only)")
            row = col.row(align=True)
            row.prop(mytool, "streaks_v", text="Threshold")
            row = col.row(align=True)
            row.prop(mytool, "streaks_n", text="Streaks")
            row = col.row(align=True)
            row.prop(mytool, "streaks_d", text="Angle offset")
        layout.prop(mytool, "use_vignette", text="Vignette")
        if mytool.use_vignette:
            layout.prop(mytool, "vignette_v", text="Amount")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(mytool, "sharpen_v", text="Sharpen")
        row = col.row(align=True)
        row.prop(mytool, "soften_v", text="Soften")

class EASYFX_PT_BlurPanel(Panel):
    bl_category = "EasyFX"
    bl_label = "Blur"
    bl_idname = "EASYFX_PT_Blur"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = context.scene
        mytool = scn.easyfx
        layout = self.layout
        layout.prop(mytool, "use_dof", text="Depth of field")
        if mytool.use_dof:
            layout.prop(mytool, "dof_v", text="F-stop")
            layout.label(text="Focal point can be set in Camera Properties")
        layout.prop(mytool, "use_speedb", text="Motion blur (Cycles only)")
        if mytool.use_speedb:
            layout.prop(mytool, "motionb_v", text="Amount")
            
class EASYFX_PT_ColorPanel(Panel):
    bl_category = "EasyFX"
    bl_label = "Color"
    bl_idname = "EASYFX_PT_Color"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = context.scene
        mytool = scn.easyfx
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(mytool, "brightness_v", text="Brightness")
        row = col.row(align=True)
        row.prop(mytool, "contrast_v", text="Contrast")
        row = col.row(align=True)
        row.prop(mytool, "bw_v", text="Saturation")
        layout.prop(mytool, "shadows_v", text="Shadows")
        layout.prop(mytool, "midtones_v", text="Midtones")
        layout.prop(mytool, "highlights_v", text="Highlights")
        
class EASYFX_PT_LensPanel(Panel):
    bl_category = "EasyFX"
    bl_label = "Lens"
    bl_idname = "EASYFX_PT_Lens"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = context.scene
        mytool = scn.easyfx
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(mytool, "lens_distort_v", text="Lens distortion")
        row = col.row(align=True)
        row.prop(mytool, "dispersion_v", text="Chromatic aberration")
        layout.prop(mytool, "use_flare", text="Lens Flare")
        if mytool.use_flare:
            layout.prop(mytool, "flare_type", text="Position")
            if mytool.flare_type == 'Fixed':
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(mytool, "flare_x", text="X")
                row.prop(mytool, "flare_y", text="Y")
                row = col.row(align=True)
                row.prop(mytool, "flare_center_size", text="Source Size")
                row = col.row(align=True)
                row.prop(mytool, "flare_c", text="")
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(mytool, "flare_streak_intensity", text='Streak Intensity')
                row = col.row(align=True)
                row.prop(mytool, "flare_streak_lenght", text="Streak Length")
                row = col.row(align=True)
                row.prop(mytool, "flare_streak_angle", text="Rotation")
                row.prop(mytool, "flare_streak_streaks", text="Streaks")
                row = col.row(align=True)
                row.prop(mytool, "flare_glow", text="Glow")
                row = col.row(align=True)
                row.prop(mytool, "flare_ghost", text="Ghost")
            else:
                layout.prop(mytool, "flare_layer", text="")
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(mytool, "flaret_streak_intensity", text='Streak Intensity')
                row = col.row(align=True)
                row.prop(mytool, "flaret_streak_lenght", text="Streak Length")
                row = col.row(align=True)
                row.prop(mytool, "flaret_streak_angle", text="Rotation")
                row.prop(mytool, "flaret_streak_streaks", text="Streaks")
                row = col.row(align=True)
                row.prop(mytool, "flaret_glow", text="Glow")
                row = col.row(align=True)
                row.prop(mytool, "flaret_ghost", text="Ghost")
        
class EASYFX_PT_WorldPanel(Panel):
    bl_category = "EasyFX"
    bl_label = "World"
    bl_idname = "EASYFX_PT_World"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = context.scene
        mytool = scn.easyfx
        layout = self.layout
        layout.prop(mytool, "use_mist", text="Mist")
        if mytool.use_mist:
            col = layout.column(align=True)
            if context.scene.render.engine != 'CYCLES':
                row = col.row(align=True)
                row.prop(mytool, "mist_sky", text="Affect sky")
            row = col.row(align=True)
            row.prop(mytool, "mist_offset", text="Offset")
            row = col.row(align=True)
            row.prop(mytool, "mist_size", text="Size")
            row = col.row(align=True)
            row.prop(mytool, "mist_min", text="Min")
            row.prop(mytool, "mist_max", text="Max")
            row = col.row(align=True)
            row.prop(mytool, "mist_color", text="")
        layout.prop(mytool, "use_transparent_sky", text="Transparent sky")
        layout.prop(mytool, "use_image_sky", text="Image sky")
        if mytool.use_image_sky:
            layout.prop(mytool, "image_sky_img", text="")
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop(mytool, "image_sky_x", text="X")
            row.prop(mytool, "image_sky_y", text="Y")
            row = col.row(align=True)
            row.prop(mytool, "image_sky_angle", text="Rotation")
            row = col.row(align=True)
            row.prop(mytool, "image_sky_scale", text="Scale")
            
class EASYFX_PT_StylePanel(Panel):
    bl_category = "EasyFX"
    bl_label = "Style"
    bl_idname = "EASYFX_PT_Style"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = context.scene
        mytool = scn.easyfx
        layout = self.layout
        layout.prop(mytool, "use_cel_shading", text="Cel shading")
        if mytool.use_cel_shading:
            layout.prop(mytool, "cel_thickness", text="Line thickness")
        layout.prop(mytool, "use_cinematic_border", text="Cinematic borders")
        if mytool.use_cinematic_border:
            layout.prop(mytool, "cinematic_border_v", text="Border height")
        
class EASYFX_PT_SettingPanel(Panel):
    bl_category = "EasyFX"
    bl_label = "Settings"
    bl_idname = "EASYFX_PT_Settings"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = context.scene
        mytool = scn.easyfx
        layout = self.layout
        layout.prop(mytool, "layer_index", text="Layer index")
        layout.operator('object.reset_settings_operator', text="Reset all values", icon="RECOVER_LAST")

# ------------------------------------------------------------------------
#   Update
# ------------------------------------------------------------------------

class EASYFX_OT_UpdateOperator(bpy.types.Operator):
    '''Update'''
    bl_idname = "object.update_operator"
    bl_label = "Update Nodes Operator"
    def execute(self, context):
        editorcheck = False
        ef_use_sky = True
        efFullscreen = False
        for area in context.screen.areas:
            if area.type == 'NODE_EDITOR':
                if area.spaces.active.tree_type != 'CompositorNodeTree':
                    area.spaces.active.tree_type = 'CompositorNodeTree'
                editorcheck = True
        if not editorcheck:
            try:
                context.area.type='NODE_EDITOR'
                context.area.ui_type = "CompositorNodeTree"
                bpy.ops.screen.area_split(factor=1)
                context.area.type='VIEW_3D'
                context.area.type='IMAGE_EDITOR'
            except:
                context.area.type='IMAGE_EDITOR'
                bpy.ops.screen.back_to_previous()  
                self.report({'WARNING'}, "Fullscreen is not supported")
                efFullscreen = True
                
        scene = context.scene
        scene.use_nodes = True
        nodes = scene.node_tree.nodes
        links = scene.node_tree.links
        
        pos_x = 200
        ef = context.scene.easyfx
        # Layer Index
        layeri = ef.layer_index
        layern = context.scene.view_layers[layeri].name
        try:
            nodes.remove(nodes['Render Layers'])
            nodes.remove(nodes['Composite'])
        except:
            pass
            
        try:
            CIn = nodes["Input"]
        except:
            CIn = nodes.new(type='CompositorNodeRLayers')
            CIn.name = "Input"
            CIn.label = "Input"
        try:
            COut = nodes["Output"]
        except:
            COut = nodes.new(type='CompositorNodeComposite')
            COut.name = "Output"
            COut.label = "Output"
        CIn.layer = layern
        latest_node = CIn
        
        global s_sky, s_cell
        
        # Transparent Sky
        if ef.use_transparent_sky:
            ef_use_sky = False
        
        # Cell Shading
        if ef.use_cel_shading:
            scene.render.line_thickness = ef.cel_thickness
            if s_cell:
                scene.render.use_freestyle = True
                self.report({'INFO'}, "Re-render Required")
                s_cell = False
        elif not ef.use_cel_shading and not s_cell:
            scene.render.use_freestyle = False
            self.report({'INFO'}, "Re-render Required")
            s_cell = True
        
        # Sharpen
        if ef.sharpen_v != 0:
            try:
                node_sharpen = nodes['Sharpen']
            except:
                node_sharpen = nodes.new(type='CompositorNodeFilter')
                node_sharpen.filter_type = 'SHARPEN'
                node_sharpen.name = 'Sharpen'
            node_sharpen.inputs[0].default_value = ef.sharpen_v
            node_sharpen.location = (pos_x,0)
            pos_x += 200
            links.new(latest_node.outputs[0], node_sharpen.inputs[1])
            latest_node = node_sharpen
        else:
            try:
                nodes.remove(nodes['Sharpen'])
            except:
                pass
        # Soften
        if ef.soften_v != 0:
            try:
                node_soften = nodes['Soften']
            except:
                node_soften = nodes.new(type='CompositorNodeFilter')
                node_soften.name = 'Soften'
            node_soften.location = (pos_x,0)
            node_soften.inputs[0].default_value = ef.soften_v
            pos_x += 200
            links.new(latest_node.outputs[0], node_soften.inputs[1])
            latest_node = node_soften
        else:
            try:
                nodes.remove(nodes['Soften'])
            except:
                pass
               
        # Speed Blur
        if ef.use_speedb and ef.motionb_v != 0:
            try:
                node_VecBlur = nodes['VecBlur']
            except:
                node_VecBlur = nodes.new(type='CompositorNodeVecBlur')
                links.new(CIn.outputs[0], node_VecBlur.inputs[0])
                node_VecBlur.name = 'VecBlur'
                node_VecBlur.label = 'Motion blur'
                links.new(CIn.outputs[2], node_VecBlur.inputs[1])
                links.new(CIn.outputs[5], node_VecBlur.inputs[2])
            node_VecBlur.location = (pos_x,0)
            node_VecBlur.factor = ef.motionb_v
            pos_x += 200
            links.new(latest_node.outputs[0], node_VecBlur.inputs[0])
            latest_node = node_VecBlur
            if scene.view_layers[layeri].use_pass_z and scene.view_layers[layeri].use_pass_vector:
                pass
            else:
                scene.view_layers[layeri].use_pass_z = True
                scene.view_layers[layeri].use_pass_vector = True
                self.report({'INFO'}, "Re-render Required")
        else:
            try:
                nodes.remove(nodes['VecBlur'])
            except:
                pass
            
        # Defocus
        if ef.use_dof:
            try:
                node_dof = nodes['DOF']
            except:
                node_dof = nodes.new(type='CompositorNodeDefocus')
                node_dof.use_zbuffer = True
                node_dof.name = 'DOF'
                node_dof.label = 'Depth of field'
                node_dof.use_preview = False
                links.new(CIn.outputs[2], node_dof.inputs[1])
            node_dof.f_stop = ef.dof_v
            node_dof.location = (pos_x,0)
            pos_x += 200
            bpy.data.cameras[0].show_limits = True
            links.new(latest_node.outputs[0], node_dof.inputs[0])
            latest_node = node_dof
            if scene.view_layers[layeri].use_pass_z:
                pass
            else:
                scene.view_layers[layeri].use_pass_z = True
                self.report({'INFO'}, "Re-render Required")
        else:
            try:
                nodes.remove(nodes['DOF'])
            except:
                pass
            
        # Color Correction
        if ef.shadows_v != ef.check_v or ef.midtones_v != ef.check_v or ef.highlights_v != ef.check_v:
            try:
                node_color = nodes['CC']
            except:
                node_color = nodes.new(type='CompositorNodeColorBalance')
                node_color.name = 'CC'
            node_color.lift = ef.shadows_v
            node_color.gamma = ef.midtones_v
            node_color.gain = ef.highlights_v
            node_color.location = (pos_x,0)
            pos_x += 450
            links.new(latest_node.outputs[0], node_color.inputs[1])
            latest_node = node_color
        else:
            try:
                nodes.remove(nodes['CC'])
            except:
                pass
            
        # Brightness/Contrast
        if ef.contrast_v != 0 or ef.brightness_v != 0:
            try:
                node_brightcont = nodes['BC']
            except:
                node_brightcont = nodes.new(type='CompositorNodeBrightContrast')
                node_brightcont.name = 'BC'
            node_brightcont.location = (pos_x,0)
            pos_x += 200
            node_brightcont.inputs[1].default_value = ef.brightness_v
            node_brightcont.inputs[2].default_value = ef.contrast_v
            links.new(latest_node.outputs[0], node_brightcont.inputs[0])
            latest_node = node_brightcont
        else:
            try:
                nodes.remove(nodes['BC'])
            except:
                pass
            
        # Mist
        if ef.use_mist:
            try:
                node_mist_mapv = nodes['Mist MapV']
                node_mist_mix = nodes['Mist Mix']
                node_mist_cramp = nodes['Mist CRamp']
            except:
                node_mist_mapv = nodes.new(type='CompositorNodeMapValue')
                node_mist_mapv.name = 'Mist MapV'
                node_mist_mapv.label = 'Mist'
                node_mist_cramp = nodes.new(type='CompositorNodeValToRGB')
                node_mist_cramp.name = 'Mist CRamp'
                node_mist_mix = nodes.new(type='CompositorNodeMixRGB')
                node_mist_mix.name = "Mist Mix"
                links.new(CIn.outputs[2], node_mist_mapv.inputs[0])
                links.new(node_mist_mapv.outputs[0], node_mist_cramp.inputs[0])
                links.new(node_mist_cramp.outputs[0], node_mist_mix.inputs[0])
            node_mist_mapv.offset[0] = -1*ef.mist_offset
            node_mist_mapv.size[0] = ef.mist_size
            if ef.mist_min != 0:
                node_mist_mapv.use_min = True
                node_mist_mapv.min[0] = ef.mist_min
            if ef.mist_max != 1:
                node_mist_mapv.use_max = True
                node_mist_mapv.max[0] = ef.mist_max
            node_mist_mix.inputs[2].default_value = ef.mist_color
            node_mist_mapv.location = (pos_x,250)
            pos_x += 200
            node_mist_cramp.location = (pos_x,250)
            pos_x += 300
            node_mist_mix.location = (pos_x,0)
            pos_x += 200
            links.new(latest_node.outputs[0], node_mist_mix.inputs[1])
            latest_node = node_mist_mix
            if ef.mist_sky == False:
                ef_use_sky = False
                try:
                    sky_layer = scene.view_layers['EasyFX - Sky']
                except:
                    sky_layer = bpy.ops.scene.render_layer_add()
                    try:
                        layx = 0
                        while True:
                            sky_layer = context.scene.view_layers[layx]
                            layx += 1
                    except:
                        sky_layer.name = 'EasyFX - Sky'
                        sky_layer.use_solid = False
                        sky_layer.use_halo = False
                        sky_layer.use_ztransp = False
                        sky_layer.use_edge_enhance = False
                        sky_layer.use_strand = False
                        sky_layer.use_freestyle = False
                    layer_active = 0
                    while layer_active < 20:
                        sky_layer.layers[layer_active] = False
                        sky_layer.layers_zmask[layer_active] = True
                        layer_active += 1
                
                try:
                    node_mist_sky = nodes['Mist_sky']
                    node_mist_alphov = nodes['Mist_alphov']
                except:
                    node_mist_sky = nodes.new(type='CompositorNodeRLayers')
                    node_mist_sky.name = 'Mist_sky'
                    node_mist_sky.label = 'Sky'
                    node_mist_sky.layer = 'EasyFX - Sky'
                    node_mist_alphov = nodes.new(type='CompositorNodeAlphaOver')
                    node_mist_alphov.name = 'Mist_alphov'
                    links.new(CIn.outputs[1], node_mist_alphov.inputs[0])
                    links.new(node_mist_sky.outputs[0], node_mist_alphov.inputs[1])
                    links.new(node_mist_mix.outputs[0], node_mist_alphov.inputs[2])
                node_mist_sky.location = (pos_x-200,-220)
                node_mist_alphov.location = (pos_x,0)
                pos_x += 200    
                latest_node = node_mist_alphov
            else:
                try:
                    nodes.remove(nodes['Mist_sky'])
                    nodes.remove(nodes['Mist_alphov'])
                except:
                    pass        
        else:
            try:
                nodes.remove(nodes['Mist MapV'])
                nodes.remove(nodes['Mist CRamp'])
                nodes.remove(nodes['Mist Mix'])
                nodes.remove(nodes['Mist_sky'])
                nodes.remove(nodes['Mist_alphov'])
            except:
                pass
        
        # Streaks
        if ef.use_streaks:
            try:
                node_streaks = nodes['Streaks']
            except:
                node_streaks = nodes.new(type='CompositorNodeGlare')
                node_streaks.name = 'Streaks'
                node_streaks.label = 'Streaks'
            node_streaks.threshold = ef.streaks_v
            node_streaks.streaks = ef.streaks_n
            node_streaks.angle_offset = ef.streaks_d

            if ef.streaks_em:
                if not scene.view_layers[layeri].use_pass_emit:
                    scene.view_layers[layeri].use_pass_emit = True
                    self.report({'INFO'}, "Re-render Required")
                links.new(CIn.outputs[17], node_streaks.inputs[0])
                try:
                    node_streaks_mix = nodes['Streaks Mix']
                except:
                    node_streaks_mix = nodes.new(type='CompositorNodeMixRGB')
                    node_streaks_mix.blend_type = 'ADD'
                    node_streaks_mix.name = 'Streaks Mix'
                links.new(latest_node.outputs[0], node_streaks_mix.inputs[1])
                links.new(node_streaks.outputs[0], node_streaks_mix.inputs[2])
                latest_node = node_streaks_mix
                node_streaks.location = (pos_x,-170)
                pos_x += 200
                node_streaks_mix.location = (pos_x,0)
                pos_x += 200
            else:
                links.new(latest_node.outputs[0], node_streaks.inputs[0])
                latest_node = node_streaks
                node_streaks.location = (pos_x,0)
                pos_x += 200
                try:
                    nodes.remove(nodes['Streaks Mix'])
                except:
                    pass
        else:
            try:
                nodes.remove(nodes['Streaks'])
                nodes.remove(nodes['Streaks Mix'])
            except:
                pass
                
        # Glow
        if ef.use_glow:
            try:
                node_glow = nodes['Glow']
            except:
                node_glow = nodes.new(type='CompositorNodeGlare')
                node_glow.glare_type = 'FOG_GLOW'
                node_glow.name = 'Glow'
                node_glow.label = 'Glow'
            node_glow.threshold = ef.glow_v
            if ef.glow_em:
                if not scene.view_layers[layeri].use_pass_emit:
                    scene.view_layers[layeri].use_pass_emit = True
                    self.report({'INFO'}, "Re-render Required")
                links.new(CIn.outputs[17], node_glow.inputs[0])
                try:
                    node_glow_mix = nodes['Glow Mix']
                except:
                    node_glow_mix = nodes.new(type='CompositorNodeMixRGB')
                    node_glow_mix.blend_type = 'ADD'
                    node_glow_mix.name = 'Glow Mix'
                    links.new(node_glow.outputs[0], node_glow_mix.inputs[2])
                links.new(latest_node.outputs[0], node_glow_mix.inputs[1])
                latest_node = node_glow_mix
                node_glow.location = (pos_x,-170)
                pos_x += 200
                node_glow_mix.location = (pos_x,0)
                pos_x += 200
            else:
                links.new(latest_node.outputs[0], node_glow.inputs[0])
                latest_node = node_glow
                node_glow.location = (pos_x,0)
                pos_x += 200
                try:
                    nodes.remove(nodes['Glow Mix'])
                except:
                    pass
        else:
            try:
                nodes.remove(nodes['Glow'])
                nodes.remove(nodes['Glow Mix'])
            except:
                pass
            
        # Image Sky
        if ef.use_image_sky:
            try:
                node_imgsky_img = nodes['Image input']
                node_imgsky_alphov = nodes['Image mix']
                node_imgsky_trans = nodes['Image transform']
            except:
                node_imgsky_img = nodes.new(type='CompositorNodeImage')
                node_imgsky_img.name = 'Image input'
                node_imgsky_alphov = nodes.new(type='CompositorNodeAlphaOver')
                node_imgsky_alphov.name = 'Image mix'
                node_imgsky_trans = nodes.new(type='CompositorNodeTransform')
                node_imgsky_trans.name = 'Image transform'
                links.new(node_imgsky_img.outputs[0], node_imgsky_trans.inputs[0])
                links.new(node_imgsky_trans.outputs[0], node_imgsky_alphov.inputs[1])
            node_imgsky_trans.inputs[1].default_value = ef.image_sky_x
            node_imgsky_trans.inputs[2].default_value = ef.image_sky_y
            node_imgsky_trans.inputs[3].default_value = ef.image_sky_angle
            node_imgsky_trans.inputs[4].default_value = ef.image_sky_scale * scene.render.resolution_percentage / 100
            links.new(latest_node.outputs[0], node_imgsky_alphov.inputs[2])
            latest_node = node_imgsky_alphov
            node_imgsky_img.location = (pos_x-400,250)
            node_imgsky_trans.location = (pos_x-200,250)
            node_imgsky_alphov.location = (pos_x,0)
            pos_x += 200
            ef_global_sky = True
            global imgs, skyimg
            if imgs != ef.image_sky_img:
                try:
                    path = r"" + bpy.path.abspath(ef.image_sky_img)
                    skyimg = bpy.data.images.load(path)
                    node_imgsky_img.image = skyimg
                except:
                    self.report({'WARNING'}, "Could not load image")
            else:  
                try:
                    node_imgsky_img.image = skyimg
                except:
                    pass
            imgs = ef.image_sky_img
            ef_use_sky = False
        else:
            try:
                nodes.remove(nodes['Image input'])
                nodes.remove(nodes['Image mix'])
                nodes.remove(nodes['Image transform'])
            except:
                pass
        
        # Lens Flare
        if ef.use_flare:
            if ef.flare_type == 'Tracked':
                try:
                    bpy.data.objects['EasyFX - Flare']
                except:
                    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=16)
                    flare_sphere = bpy.context.object
                    flare_sphere.name = 'EasyFX - Flare'
                    mat = bpy.data.materials.new("EasyFX - Flare")
                    mat.specular_intensity = 0
                    mat.emit = 5
                    flare_sphere.data.materials.append(mat)
                try:
                    flare_layer = bpy.context.scene.view_layers['EasyFX - Flare']
                except:
                    flare_layer = bpy.ops.scene.render_layer_add()
                    try:
                        layx = 0
                        while True:
                            flare_layer = bpy.context.scene.view_layers[layx]
                            layx += 1
                    except:
                        flare_layer.name = 'EasyFX - Flare'
                        flare_layer.use_sky = False
                    layer_active = 0
                    while layer_active < 20:
                        flare_layer.layers[layer_active] = False
                        flare_layer.layers_zmask[layer_active] = True
                        layer_active += 1
                flare_layer.layers = ef.flare_layer
                bpy.ops.object.move_to_layer(layers=ef.flare_layer)
            if ef.flare_type == 'Fixed':
                pos_x -= 600
                try:
                    nodes.remove(nodes['flare_rlayer'])
                except:
                    pass    
                try:
                    node_flare_mask1 = nodes['flare_mask1']
                    node_flare_rgb = nodes['flare_rgb']
                    node_flare_dist1 = nodes['flare_dist1']
                    node_flare_dist2 = nodes['flare_dist2']
                    node_flare_mask2 = nodes['flare_mask2']
                    node_flare_mixc = nodes['flare_mixc']
                    node_flare_trans = nodes['flare_translate']
                    node_flare_alphov = nodes['flare_alphaover']
                    node_flare_ckey = nodes['flare_ckey']
                except:
                    node_flare_mask1 = nodes.new(type='CompositorNodeMask')
                    node_flare_mask1.size_source = 'FIXED'
                    node_flare_mask1.name = 'flare_mask1'
                    node_flare_rgb = nodes.new(type='CompositorNodeRGB')
                    node_flare_rgb.name = 'flare_rgb'
                    node_flare_rgb.label = 'Flare Color'
                    node_flare_dist1 = nodes.new(type='CompositorNodeLensdist')
                    node_flare_dist1.inputs[1].default_value = 1
                    node_flare_dist1.name = 'flare_dist1'
                    node_flare_dist2 = nodes.new(type='CompositorNodeLensdist')
                    node_flare_dist2.inputs[1].default_value = 1
                    node_flare_dist2.name = 'flare_dist2'
                    node_flare_mixc = nodes.new(type='CompositorNodeMixRGB')
                    node_flare_mixc.blend_type = 'ADD'
                    node_flare_mixc.name = 'flare_mixc'
                    node_flare_trans = nodes.new(type='CompositorNodeTranslate')
                    node_flare_trans.name = 'flare_translate'
                    node_flare_mask2 = nodes.new(type='CompositorNodeMask')
                    node_flare_mask2.name = 'flare_mask2'
                    node_flare_alphov = nodes.new(type='CompositorNodeAlphaOver')
                    node_flare_alphov.name = 'flare_alphaover'
                    node_flare_ckey = nodes.new(type='CompositorNodeChromaMatte')
                    node_flare_ckey.name = 'flare_ckey'
                    node_flare_ckey.tolerance = 1
                    node_flare_ckey.threshold = 1
                    node_flare_ckey.gain = 0
                    node_flare_ckey.inputs[1].default_value = (0, 0, 0, 1)
                    links.new(node_flare_mask1.outputs[0], node_flare_dist1.inputs[0])
                    links.new(node_flare_dist1.outputs[0], node_flare_mixc.inputs[1])
                    links.new(node_flare_rgb.outputs[0], node_flare_dist2.inputs[0])
                    links.new(node_flare_dist2.outputs[0], node_flare_mixc.inputs[2])
                    links.new(node_flare_mixc.outputs[0], node_flare_trans.inputs[0])
                    links.new(node_flare_trans.outputs[0], node_flare_alphov.inputs[2])
                    links.new(node_flare_mask2.outputs[0], node_flare_alphov.inputs[1])
                    links.new(node_flare_alphov.outputs[0], node_flare_ckey.inputs[0])
                node_flare_rgb.outputs[0].default_value = ef.flare_c
                node_flare_trans.inputs[1].default_value = ef.flare_x
                node_flare_trans.inputs[2].default_value = ef.flare_y
                node_flare_layer = node_flare_ckey
                node_flare_mask1.size_x = ef.flare_center_size
                node_flare_mask1.size_y = ef.flare_center_size
                node_flare_mask1.location = (pos_x, -450)
                node_flare_rgb.location = (pos_x, -700)
                pos_x += 200
                node_flare_dist1.location = (pos_x, -450)
                node_flare_dist2.location = (pos_x, -700)
                pos_x += 200
                node_flare_mixc.location = (pos_x, -450)
                pos_x += 200
                node_flare_trans.location = (pos_x, -450)
                node_flare_mask2.location = (pos_x, -200)
                pos_x += 200
                node_flare_alphov.location = (pos_x, -200)
                pos_x += 200
                node_flare_ckey.location = (pos_x, -200)
                pos_x += 200
            else:
                try:
                    nodes.remove(nodes['flare_mask1'])
                    nodes.remove(nodes['flare_rgb'])
                    nodes.remove(nodes['flare_dist1'])
                    nodes.remove(nodes['flare_dist2'])
                    nodes.remove(nodes['flare_mask2'])
                    nodes.remove(nodes['flare_mixc'])
                    nodes.remove(nodes['flare_translate'])
                    nodes.remove(nodes['flare_alphaover'])
                    nodes.remove(nodes['flare_ckey'])
                except:
                    pass        
                try:
                    node_flare_layer = nodes['flare_rlayer']
                except:
                    node_flare_layer = nodes.new(type='CompositorNodeRLayers')
                    node_flare_layer.name = 'flare_rlayer'
                    node_flare_layer.layer = 'EasyFX - Flare'
                node_flare_layer.location = (pos_x-200, -600)
            try:
                node_flare_ghost = nodes['flare_ghost']
                node_flare_glow = nodes['flare_glow']
                node_flare_streaks = nodes['flare_streaks']
                node_flare_tonemap = nodes['flare_tonemap']
                node_flare_mix1 = nodes['flare_mix1']
                node_flare_mix2 = nodes['flare_mix2']
                node_flare_mix3 = nodes['flare_mix3']
                node_flare_tonemap2 = nodes['flare_tonemap2']
            except:        
                node_flare_ghost = nodes.new(type='CompositorNodeGlare')
                node_flare_ghost.glare_type = 'GHOSTS'
                node_flare_ghost.threshold = 0
                node_flare_ghost.name = 'flare_ghost'
                node_flare_glow = nodes.new(type='CompositorNodeGlare')
                node_flare_glow.glare_type = 'FOG_GLOW'
                node_flare_glow.threshold = 0
                node_flare_glow.quality = 'LOW'
                node_flare_glow.name = 'flare_glow'
                node_flare_streaks = nodes.new(type='CompositorNodeGlare')
                node_flare_streaks.glare_type = 'STREAKS'
                node_flare_streaks.threshold = 0
                node_flare_streaks.streaks = 12
                node_flare_streaks.quality = 'LOW'
                node_flare_streaks.name = 'flare_streaks'
                node_flare_streaks.angle_offset = 10 * math.pi / 180
                node_flare_tonemap = nodes.new(type='CompositorNodeTonemap')
                node_flare_tonemap.tonemap_type = 'RH_SIMPLE'
                node_flare_tonemap.key = 0.007
                node_flare_tonemap.name = 'flare_tonemap'
                node_flare_mix1 = nodes.new(type='CompositorNodeMixRGB')
                node_flare_mix1.blend_type = 'SCREEN'
                node_flare_mix1.name = 'flare_mix1'
                node_flare_mix2 = nodes.new(type='CompositorNodeMixRGB')
                node_flare_mix2.blend_type = 'SCREEN'
                node_flare_mix2.name = 'flare_mix2'
                node_flare_mix3 = nodes.new(type='CompositorNodeMixRGB')
                node_flare_mix3.blend_type = 'SCREEN'
                node_flare_mix3.name = 'flare_mix3'
                node_flare_tonemap2 = nodes.new(type='CompositorNodeTonemap')
                node_flare_tonemap2.tonemap_type = 'RH_SIMPLE'
                node_flare_tonemap2.name = 'flare_tonemap2'
                links.new(node_flare_mix2.outputs[0], node_flare_mix3.inputs[2])
                links.new(node_flare_mix1.outputs[0], node_flare_mix2.inputs[1])
                links.new(node_flare_streaks.outputs[0], node_flare_mix2.inputs[2])
                links.new(node_flare_tonemap.outputs[0], node_flare_mix1.inputs[1])
                links.new(node_flare_ghost.outputs[0], node_flare_mix1.inputs[2])
                links.new(node_flare_glow.outputs[0], node_flare_tonemap.inputs[0])
                links.new(node_flare_streaks.outputs[0], node_flare_tonemap2.inputs[0])
                links.new(node_flare_tonemap2.outputs[0], node_flare_mix2.inputs[2])
            links.new(node_flare_layer.outputs[0], node_flare_ghost.inputs[0])   
            links.new(node_flare_layer.outputs[0], node_flare_glow.inputs[0])
            links.new(node_flare_layer.outputs[0], node_flare_streaks.inputs[0]) 
            links.new(latest_node.outputs[0], node_flare_mix3.inputs[1])
            latest_node = node_flare_mix3
            node_flare_ghost.location = (pos_x, -200)
            node_flare_glow.location = (pos_x, -450)
            node_flare_streaks.location = (pos_x, -680)
            pos_x += 200
            node_flare_tonemap.location = (pos_x, -350)
            pos_x += 200
            node_flare_tonemap2.location = (pos_x, -400)
            node_flare_mix1.location = (pos_x, -200)
            pos_x += 200
            node_flare_mix2.location = (pos_x, -200)
            pos_x += 200
            node_flare_mix3.location = (pos_x, 0)
            pos_x += 200
            if ef.flare_type == 'Fixed':
                node_flare_tonemap.key = 0.03
                node_flare_tonemap2.location = (pos_x-600, -550)
                node_flare_tonemap2.offset = 10
                node_flare_streaks.iterations = 5
                node_flare_streaks.quality = 'MEDIUM'
                node_flare_streaks.fade = 0.92
                node_flare_ghost.iterations = 4
                node_flare_tonemap2.key = ef.flare_streak_intensity
                node_flare_tonemap2.gamma = ef.flare_streak_lenght
                node_flare_streaks.angle_offset = ef.flare_streak_angle
                node_flare_streaks.streaks = ef.flare_streak_streaks
                node_flare_tonemap.key = ef.flare_glow
                node_flare_mix1.inputs[0].default_value = ef.flare_ghost
            else:
                node_flare_tonemap2.key = ef.flaret_streak_intensity
                node_flare_tonemap2.gamma = ef.flaret_streak_lenght
                node_flare_streaks.angle_offset = ef.flaret_streak_angle
                node_flare_streaks.streaks = ef.flaret_streak_streaks
                node_flare_tonemap.key = ef.flaret_glow
                node_flare_mix1.inputs[0].default_value = ef.flaret_ghost    
        else:
            try:
                nodes.remove(nodes['flare_ghost'])
                nodes.remove(nodes['flare_glow'])
                nodes.remove(nodes['flare_streaks'])
                nodes.remove(nodes['flare_tonemap'])
                nodes.remove(nodes['flare_mix1'])
                nodes.remove(nodes['flare_mix2'])
                nodes.remove(nodes['flare_mix3'])
                nodes.remove(nodes['flare_tonemap2'])
                nodes.remove(nodes['flare_rlayer'])
            except:
                pass
            try:
                nodes.remove(nodes['flare_mask1'])
                nodes.remove(nodes['flare_rgb'])
                nodes.remove(nodes['flare_dist1'])
                nodes.remove(nodes['flare_dist2'])
                nodes.remove(nodes['flare_mask2'])
                nodes.remove(nodes['flare_mixc'])
                nodes.remove(nodes['flare_translate'])
                nodes.remove(nodes['flare_alphaover'])
                nodes.remove(nodes['flare_ckey'])
            except:
                pass
        
        # BW Saturation
        if ef.bw_v != 1:
            try:
                node_bw = nodes['ColorC']
            except:
                node_bw = nodes.new(type='CompositorNodeColorCorrection')
                node_bw.name = 'ColorC'
            links.new(latest_node.outputs[0], node_bw.inputs[0])
            node_bw.master_saturation = ef.bw_v
            node_bw.location = (pos_x,0)
            pos_x += 450
            latest_node = node_bw
        else:
            try:
                nodes.remove(nodes['ColorC'])
            except:
                pass    
        
        # Lens Distortion
        if ef.lens_distort_v != 0:
            try:
                node_lensdist = nodes['LensDist']
            except:
                node_lensdist = nodes.new(type='CompositorNodeLensdist')
                node_lensdist.name = 'LensDist'
            node_lensdist.inputs[2].default_value = ef.lens_distort_v
            node_lensdist.inputs[1].default_value = ef.dispersion_v
            node_lensdist.location = (pos_x,0)
            pos_x += 200
            links.new(latest_node.outputs[0], node_lensdist.inputs[0])
            latest_node = node_lensdist
        else:
            try:
                nodes.remove(nodes['LensDist'])
            except:
                pass
            
        # Vignette
        if ef.use_vignette:
            try:
                node_ellips_mask = nodes['Ellips']
                node_vign_mul = nodes['Mul']
                node_vign_blur = nodes['Blur']
            except:
                node_ellips_mask = nodes.new(type='CompositorNodeEllipseMask')
                node_ellips_mask.name = 'Ellips'
                node_vign_blur = nodes.new(type='CompositorNodeBlur')
                node_vign_blur.name = 'Blur'
                node_vign_blur.size_x = 800
                node_vign_blur.size_y = 800
                node_vign_blur.use_relative = True
                node_vign_mul = nodes.new(type='CompositorNodeMixRGB')
                node_vign_mul.blend_type = 'MULTIPLY'
                node_vign_mul.inputs[0].default_value = 0.75
                node_vign_mul.inputs[1].default_value = (0, 0, 0, 1)
                node_vign_mul.name = 'Mul'
                links.new(node_ellips_mask.outputs[0], node_vign_blur.inputs[0])
                links.new(node_vign_blur.outputs[0], node_vign_mul.inputs[2])
            node_vign_blur.factor = ef.vignette_v/100
            node_ellips_mask.location = (pos_x,300)
            node_vign_blur.location = (pos_x+200,300)
            node_vign_mul.location = (pos_x+400,0)
            links.new(latest_node.outputs[0], node_vign_mul.inputs[1])
            latest_node = node_vign_mul
        else:
            try:
                nodes.remove(nodes['Ellips'])
                nodes.remove(nodes['Mul'])
                nodes.remove(nodes['Blur'])
            except:
                pass
            
        # Cinematic Borders
        if ef.use_cinematic_border:
            try:
                node_border = nodes['CineBorder']
            except:
                node_border = nodes.new(type='CompositorNodeScale')
                node_border.space = 'RELATIVE'
                node_border.name = 'CineBorder'
            node_border.inputs[1].default_value = (1, ef.cinematic_border_v)
            node_border.location = (pos_x,0)
            pos_x += 200
            links.new(latest_node.outputs[0], node_border.inputs[0])
            latest_node = node_border
        else:
            try:
                nodes.remove(nodes['CineBorder'])
            except:
                pass
        
        # Compose Sky
        if ef_use_sky:
            try:
                nodes.remove(nodes['Sky Input'])
                nodes.remove(nodes['Sky Alpha Over'])
            except:
                pass
            try:
                node_sky_input = nodes['Sky Input']
                node_sky_alphov = nodes['Sky Alpha Over']
            except:
                node_sky_input = nodes.new(type='CompositorNodeRLayers')
                node_sky_input.name = 'Sky Input'
                node_sky_input.label = 'Sky'
                node_sky_alphov = nodes.new(type='CompositorNodeAlphaOver')
                node_sky_alphov.name = 'Sky Alpha Over'
                links.new(node_sky_input.outputs[0], node_sky_alphov.inputs[1])
                links.new(latest_node.outputs[0], node_sky_alphov.inputs[2])
            node_sky_input.layer = 'Sky'
            node_sky_input.location = (pos_x-200, -250)
            node_sky_alphov.location = (pos_x, 0)
            pos_x += 200
            latest_node = node_sky_alphov
        
        links.new(latest_node.outputs[0], COut.inputs[0])
        latest_node = node_sky_alphov
        
        return {'FINISHED'}

# ------------------------------------------------------------------------
#   Update & Render
# ------------------------------------------------------------------------

class EASYFX_OT_RenderOperator(bpy.types.Operator):
    '''Update & Render'''
    bl_idname = "object.update_render_operator"
    bl_label = "Update & Render Operator"
    def execute(self, context):
        bpy.ops.object.update_operator()
        bpy.ops.render.render('INVOKE_DEFAULT')
        return {'FINISHED'}

class EASYFX_OT_ResetOperator(bpy.types.Operator):
    '''Reset all values'''
    bl_idname = "object.reset_settings_operator"
    bl_label = "Reset all values"
    def execute(self, context):
        wm = bpy.context.scene.easyfx
        for prop in wm.bl_rna.properties:
            if not prop.is_readonly:
                setattr(wm, prop.identifier, prop.default)
        return {'FINISHED'}

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MySettings,
    EASYFX_PT_UpdatePanel,
    EASYFX_PT_FilterPanel,
    EASYFX_PT_BlurPanel,
    EASYFX_PT_ColorPanel,
    EASYFX_PT_LensPanel,
    EASYFX_PT_WorldPanel,
    EASYFX_PT_StylePanel,
    EASYFX_PT_SettingPanel,
    EASYFX_OT_UpdateOperator,
    EASYFX_OT_RenderOperator,
    EASYFX_OT_ResetOperator
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.easyfx = PointerProperty(type=MySettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.easyfx

if __name__ == "__main__":
    register()
