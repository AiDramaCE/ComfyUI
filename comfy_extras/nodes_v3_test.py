import torch
from comfy_api.v3 import io
import logging
import folder_paths
import comfy.utils
import comfy.sd
from typing import Any

@io.comfytype(io_type="XYZ")
class XYZ:
    Type = tuple[int,str]
    class Input(io.InputV3):
        ...
    class Output(io.OutputV3):
        ...


class V3TestNode(io.ComfyNodeV3):
    class State(io.NodeState):
        my_str: str
        my_int: int
    state: State

    def __init__(self):
        super().__init__()
        self.hahajkunless = ";)"

    @classmethod
    def DEFINE_SCHEMA(cls):
        return io.SchemaV3(
            node_id="V3_01_TestNode1",
            display_name="V3 Test Node",
            category="v3 nodes",
            description="This is a funky V3 node test.",
            inputs=[
                io.Image.Input("image", display_name="new_image"),
                XYZ.Input("xyz", optional=True),
                io.Custom("JKL").Input("jkl", optional=True),
                io.Mask.Input("mask", optional=True),
                io.Int.Input("some_int", display_name="new_name", min=0, max=127, default=42,
                             tooltip="My tooltip 😎", display_mode=io.NumberDisplay.slider, types=[io.Float]),
                io.Combo.Input("combo", options=["a", "b", "c"], tooltip="This is a combo input", types=[io.Mask]),
                io.MultiCombo.Input("combo2", options=["a","b","c"]),
                io.MultiType.Input("multitype", types=[io.Mask, io.Float, io.Int], optional=True),
                # ComboInput("combo", image_upload=True, image_folder=FolderType.output,
                #             remote=RemoteOptions(
                #                 route="/internal/files/output",
                #                 refresh_button=True,
                #             ),
                #             tooltip="This is a combo input"),
                # IntegerInput("some_int", display_name="new_name", min=0, tooltip="My tooltip 😎", display=NumberDisplay.slider, ),
                # ComboDynamicInput("mask", behavior=InputBehavior.optional),
                # IntegerInput("some_int", display_name="new_name", min=0, tooltip="My tooltip 😎", display=NumberDisplay.slider,
                #              dependent_inputs=[ComboDynamicInput("mask", behavior=InputBehavior.optional)],
                #              dependent_values=[lambda my_value: IO.STRING if my_value < 5 else IO.NUMBER],
                #              ),
                # ["option1", "option2". "option3"]
                # ComboDynamicInput["sdfgjhl", [ComboDynamicOptions("option1", [IntegerInput("some_int", display_name="new_name", min=0, tooltip="My tooltip 😎", display=NumberDisplay.slider, ImageInput(), MaskInput(), String()]),
                #                              CombyDynamicOptons("option2", [])
                #                                                   ]]
            ],
            outputs=[
                io.Int.Output("int_output"),
                io.Image.Output("img_output", display_name="img🖼️", tooltip="This is an image"),
            ],
            hidden=[
                io.Hidden.prompt,
                io.Hidden.auth_token_comfy_org,
                io.Hidden.unique_id,
            ],
            is_output_node=True,
        )

    @classmethod
    def execute(cls, image: io.Image.Type, some_int: int, combo: io.Combo.Type, combo2: io.MultiCombo.Type, xyz: XYZ.Type=None, mask: io.Mask.Type=None, **kwargs):
        zzz = cls.hidden.prompt
        cls.state.my_str = "LOLJK"
        expected_int = 123
        if "thing" not in cls.state:
            cls.state["thing"] = "hahaha"
            yyy = cls.state["thing"]
            del cls.state["thing"]
        if cls.state.get_value("int2") is None:
            cls.state.set_value("int2", 123)
            zzz = cls.state.get_value("int2")
            cls.state.pop("int2")
        if cls.state.my_int is None:
            cls.state.my_int = expected_int
        else:
            if cls.state.my_int != expected_int:
                raise Exception(f"Explicit state object did not maintain expected value (__getattr__/__setattr__): {cls.state.my_int} != {expected_int}")
        #some_int
        if hasattr(cls, "hahajkunless"):
            raise Exception("The 'cls' variable leaked instance state between runs!")
        if hasattr(cls, "doohickey"):
            raise Exception("The 'cls' variable leaked state on class properties between runs!")
        cls.doohickey = "LOLJK"
        return io.NodeOutput(some_int, image)


class V3LoraLoader(io.ComfyNodeV3):
    class State(io.NodeState):
        loaded_lora: tuple[str, Any] | None = None
    state: State

    @classmethod
    def DEFINE_SCHEMA(cls):
        return io.SchemaV3(
            node_id="V3_LoraLoader",
            display_name="V3 LoRA Loader",
            category="v3 nodes",
            description="LoRAs are used to modify diffusion and CLIP models, altering the way in which latents are denoised such as applying styles. Multiple LoRA nodes can be linked together.",
            inputs=[
                io.Model.Input("model", tooltip="The diffusion model the LoRA will be applied to."),
                io.Clip.Input("clip", tooltip="The CLIP model the LoRA will be applied to."),
                io.Combo.Input(
                    "lora_name",
                    options=folder_paths.get_filename_list("loras"),
                    tooltip="The name of the LoRA."
                ),
                io.Float.Input(
                    "strength_model",
                    default=1.0,
                    min=-100.0,
                    max=100.0,
                    step=0.01,
                    tooltip="How strongly to modify the diffusion model. This value can be negative."
                ),
                io.Float.Input(
                    "strength_clip",
                    default=1.0,
                    min=-100.0,
                    max=100.0,
                    step=0.01,
                    tooltip="How strongly to modify the CLIP model. This value can be negative."
                ),
            ],
            outputs=[
                io.Model.Output("model_out"),
                io.Clip.Output("clip_out"),
            ],
        )

    @classmethod
    def execute(cls, model: io.Model.Type, clip: io.Clip.Type, lora_name: str, strength_model: float, strength_clip: float, **kwargs):
        if strength_model == 0 and strength_clip == 0:
            return io.NodeOutput(model, clip)

        lora_path = folder_paths.get_full_path_or_raise("loras", lora_name)
        lora = None
        if cls.state.loaded_lora is not None:
            if cls.state.loaded_lora[0] == lora_path:
                lora = cls.state.loaded_lora[1]
            else:
                cls.state.loaded_lora = None

        if lora is None:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            cls.state.loaded_lora = (lora_path, lora)

        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
        return io.NodeOutput(model_lora, clip_lora)


NODES_LIST: list[type[io.ComfyNodeV3]] = [
    V3TestNode,
    V3LoraLoader,
]
