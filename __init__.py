import bpy
import os
import subprocess

bl_info = {
    "name": "Blender to Substance painter",
    "description": "Export a mesh to Substance painter",
    "author": "Name",
    "version": (0, 1),
    "blender": (4, 2, 3),
    "location": "View3D > UI > Tools",
    "warning": "",  # used for warning icon and text in addons panel
    "doc_url": "TBA",
    "tracker_url": "TBA",
    "support": "COMMUNITY",
    "category": "Exporter",
}
'''

TODO
refactor code, variables, make it easier to read and structure it
a proper MD for the repo
add more messages incase something doesnt exist (bump_map example)
'''


#Move paths to seperate file or make them dynamic
class textureSettings(bpy.types.PropertyGroup):
    use_normal_map: bpy.props.BoolProperty(
    name="use_normal_map",
    description="Enable to use Normal Map",
    default=True,
    )
    use_height_map: bpy.props.BoolProperty(
    name="use_height_map",
    description="Enable to use Height Map",
    default=False,
    )
    use_bump_map: bpy.props.BoolProperty(
    name="use_bump_map",
    description="Enable to use Bump Map",
    default=False,
    ) 
    

class EXPORT_OT_Substancepainter_exporter(bpy.types.Operator):
    bl_idname = "export.substance_painter"
    bl_label = "Export to Substance Painter"
    
    # Base paths
    export_folder = os.path.normpath("C:/Substancepainter/FBX")
    
    substance_painter_path = os.path.normpath(
        "C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe")

    def execute(self, context):
        # Ensure export folder exists
        if not os.path.exists(self.export_folder):
            os.makedirs(self.export_folder)
        # Get selected objects
        objects = context.selected_objects
        if not objects : 
            self.report({"WARNING"}, "No object selected")
        # Export each object and track success
        try:
            for obj in objects:
                if self.export_object(obj):
                    self.report({"INFO"},f"Successfully exported {obj.name}")
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export {obj.name}, the error: {str(e)}")
        return {'FINISHED'}
    

    def material_check(self,obj):

        if len(obj.data.materials) == 0: 
            
            self.report({"INFO"}, f"No material on { obj.name}, creating new one")            
            new_material = bpy.data.materials.new(name=f"{obj.name}_material")
            new_material.use_nodes = True  # Enable nodes if you want shader control
            obj.data.materials.append(new_material)
            self.report({"INFO"}, f"{obj.name} has a {obj.name}_material added to it")
        else:
            self.report({"INFO"}, f"{obj.name} already has an material")



    def export_object(self, obj):
    # Set dynamic path for each object
            if obj.type == 'MESH':
        
                self.material_check(obj)
                #Create object folder
                object_folder = os.path.join(self.export_folder, obj.name)
                os.makedirs(object_folder, exist_ok=True)

                # Create a texture folder inside the object folder
                texture_folder_name = f"{obj.name}_textures" 
                texture_folder = os.path.join(object_folder, texture_folder_name)
                os.makedirs(texture_folder, exist_ok=True)
                
                #Set final exportpath and name
                export_name = f"{obj.name}.fbx"
                export_path = os.path.normpath(os.path.join(object_folder, export_name))

                # Export the selected object
                file = bpy.ops.export_scene.fbx(filepath=export_path, 
                                                global_scale=1.0, 
                                                apply_unit_scale=True, 
                                                use_selection=True)
                # Print info
                self.report({"INFO"}, f"Exported {obj.name} to {file}")
                self.report({"INFO"}, f"Opening {obj.name} in Substance Painter")


                #Normalize the path
                object_path = export_path.replace("\\", "/")
                # Attempt to open substance painter
                self.open_substancepainter(object_path)
                self.report({"INFO"}, f"object path {object_path}")
                return object_path
            else:    
                self.report({"WARNING"}, f"{obj.name} is not a mesh object, skipping mesh check.")
                return False

    def open_substancepainter(self,File):
        try:
            args = [self.substance_painter_path, "--mesh", File]
            subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
            # Run Substance Painter
            self.report({"INFO"}, f"Trying to open Substance Painter at {str(self.substance_painter_path)} with FBX {File}")
        except Exception as e:
            self.report(
                {'ERROR'}, f"Could not open Substance Painter: {str(e)}, {str(self.substance_painter_path)},{str(File)}")


#one object at a time! test with multiple, check if in object mode




class IMPORT_OT_Textures(bpy.types.Operator):
    bl_idname ="import.textures"
    bl_label = "import Textures"
     
    use_normal_map= bpy.props.BoolProperty(
    name="use_normal_map",
    description="Enable to use Normal Map",
    default=True,
    )
    use_height_map= bpy.props.BoolProperty(
        name="use_height_map",
        description="Enable to use Height Map",
        default=False,
    )
    use_bump_map= bpy.props.BoolProperty(
        name="use_bump_map",
        description="Enable to use Bump Map",
        default=False,
    ) 
    
    
    def execute(self,context):
        #Get active object
        obj = bpy.context.active_object
        #texture folder for object:
        textures_folder = os.path.join(os.path.normpath("C:/Substancepainter/FBX"),obj.name,f"{obj.name}_textures")        
       

        try:
            if not textures_folder.find(obj.name): 
                self.report({"INFO"}, f"Texture folder does not exist for {str(obj.name)}")

                
            if not textures_folder:
                self.report({"INFO"}, f"Texture folder {str(textures_folder)} does not exist")
                

            #Validate selection
            if not obj or obj.type !="MESH":
                self.report({"INFO"}, "Object is not a mesh or no object is selected")
            
            
            #Validate material, incase export function hasnt been used
            if not obj.data.materials:
                mat = bpy.data.materials.new(new=f"{obj.name}_Material")
                mat.use_nodes = True
                obj.data.materials.append(mat)
            material = obj.data.materials[0]
            #if material already exists, check if nodes are used
            if not material.use_nodes:
                material.use_nodes = True
            #Call assign textures method
            self.assign_textures(material,textures_folder,context.scene.texture_settings)
            return {"FINISHED"}
        except Exception as e:
            self.report({"INFO"}, f"Texture folder does not exist for {str(obj.name)}")
            return {"CANCELLED"}
        


        #obs! make sure node wrangler is enabled
    def assign_textures(self,material,textures_folder,texture_settings):
        #nodes and links of material
        node_tree = material.node_tree
        nodes = node_tree.nodes
        links = node_tree.links
        file_types = (".png",".jpg",".jpeg")
        node_x_displacement = 400 
        # Remove previous nodes to clear the workspace
        for node in nodes:
            nodes.remove(node)

        # create BSDF and output node
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        output_node.location = (400, 0)

        principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
        principled_node.location = (0, 0)

        # Link the Principled BSDF to the Material Output
        links.new(principled_node.outputs["BSDF"], output_node.inputs["Surface"])

        # assign textures to material:
        for index, filename in enumerate(os.listdir(textures_folder)):
            #check filetypes and join them
            if filename.lower().endswith(file_types):
                texture_type = self.get_texture_type(filename)
                filepath = os.path.join(textures_folder, filename)

                #Create an image node and apply texture 
                image_node = nodes.new(type="ShaderNodeTexImage")
                image_node.location = (-800, -400*index )
                image_node.image = bpy.data.images.load(filepath)
                #align better to bsdf
                image_node.location.y += 800
                #connect to BSDF
                if texture_type == "Base Color":
                    links.new(image_node.outputs["Color"], principled_node.inputs["Base Color"])
                elif texture_type == "Roughness":
                    links.new(image_node.outputs["Color"], principled_node.inputs["Roughness"])
                elif texture_type == "Metallic":
                    links.new(image_node.outputs["Color"], principled_node.inputs["Metallic"])
                    
                #Check that these maps exist in the first place
                elif texture_type == "Normal" and texture_settings.use_normal_map :
                    normal_node = nodes.new(type="ShaderNodeNormalMap")
                    normal_node.location = (image_node.location.x +node_x_displacement, image_node.location.y)
                    links.new(image_node.outputs["Color"], normal_node.inputs["Color"])
                    links.new(normal_node.outputs["Normal"], principled_node.inputs["Normal"])

                elif texture_type == "Height" and texture_settings.use_height_map :
                    Height_node = nodes.new(type="ShaderNodeDisplacement")
                    Height_node.location = (image_node.location.x+node_x_displacement, image_node.location.y)
                    links.new(image_node.outputs["Color"], Height_node.inputs["Normal"])
                    links.new(Height_node.outputs["Displacement"], principled_node.inputs["Normal"])
                    
                elif texture_type == "Bump" and texture_settings.use_bump_map :
                    bump_node = nodes.new(type="ShaderNodeBump")
                    bump_node.location = (image_node.location.x+node_x_displacement, image_node.location.y)
                    links.new(image_node.outputs["Color"], bump_node.inputs["Normal"])
                    links.new(bump_node.outputs["Normal"], principled_node.inputs["Normal"])
      
                                        
    def get_texture_type(self, filename):
            """
            Check  texture type based on the filename.
            """
            if "diffuse" in filename.lower() or "base_color" in filename.lower():
                return "Base Color"
            elif "roughness" in filename.lower():
                return "Roughness"
            elif "normal" in filename.lower():
                return "Normal"
            elif "height" in filename.lower():
                return "Height"
            elif "metallic" in filename.lower():
                return "Metallic"
            
            else:
                return None      
              
class REMOVE_OT_UNUSED_TEXTURES(bpy.types.Operator):
    '''Clears any unused texture nodes'''
    bl_idname = "remove.unusedtextures"
    bl_label = "Remove unused textures in material"
    def execute(self, context):
        obj = bpy.context.active_object
        if not obj.data.materials or obj is None:
            bpy.context.report({"WARNING"}, text="Object has no material or no object has been selected")
        nodes = obj.data.materials[0].node_tree.nodes
        for node in nodes: 
            try:
                if isinstance(node,bpy.types.ShaderNodeTexImage):
                    
                    if len(node.outputs[0].links) ==0:
                        nodes.remove(node)

            except Exception as e:
                self.report({"INFO"}, f"An Error has occured: {e}")
                
        #realign the existing nodes?
        self.realign_nodes(nodes)
        
        return {'FINISHED'}
    def realign_nodes(self, nodes):
        """
        Realign the texture nodes for better structure
        """
        y_offset = 0
        node_spacing = 300  # Adjust the spacing between nodes as needed
        
        #Arrange nodes, check only color output in shadernodeteximage
        for node in nodes:
            if isinstance(node,bpy.types.ShaderNodeTexImage):
                node.location.y = y_offset
                y_offset -= node_spacing
                            

    

class OPEN_OT_FBXFolder(bpy.types.Operator):
    """Opens the FBX Export Folder"""
    bl_idname = "open.fbx_folder"
    bl_label = "Open FBX Folder"

    def execute(self, context):
        export_folder = os.path.normpath("C:/Substancepainter/FBX")
        try:
            os.startfile(export_folder)  
            self.report({'INFO'}, f"Opened folder: {export_folder}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open folder: {str(e)}")
        return {'FINISHED'}




class VIEW3D_PT_QuickExporter(bpy.types.Panel):
    """UI Panel for quick export to Substance Painter"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick Export"
    bl_label = "Quick Exporter"


    def draw(self, context):
        scene = context.scene
        layout = self.layout
        texturesettings = context.scene.texture_settings

        row = layout.row()
        row.operator(EXPORT_OT_Substancepainter_exporter.bl_idname,
                     text="Export to Substance Painter")
        row = layout.row()
        row.operator(OPEN_OT_FBXFolder.bl_idname,
                     text="Open the fbx folder")
        row = layout.row()
        row.operator(IMPORT_OT_Textures.bl_idname,
                     text="Import Textures from Substance Painter")
        #register checkboxes in UI 
        layout.label(text="Import settings")
        layout.prop(texturesettings, "use_normal_map", text="Normal Map")
        layout.prop(texturesettings, "use_height_map", text="Height Map")
        layout.prop(texturesettings, "use_bump_map", text="Bump Map")
        layout.label(text="Cleanup functions")
        row = layout.row()
        row.operator(REMOVE_OT_UNUSED_TEXTURES.bl_idname,
                     text="Remove unused textures")
        

classes = (textureSettings,VIEW3D_PT_QuickExporter, EXPORT_OT_Substancepainter_exporter,OPEN_OT_FBXFolder,IMPORT_OT_Textures,REMOVE_OT_UNUSED_TEXTURES)


def register():
# storing property in scene for this example
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.texture_settings = bpy.props.PointerProperty(type=textureSettings)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.texture_settings

if __name__ == "__main__":
    register()