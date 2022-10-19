import onnxruntime as ort

class InferenceManager():
    def __init__(self):
        self.save_weights_path = "/usr/src/app/src/server/libs/weights/model.onnx"
        self.providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.session = ort.InferenceSession(self.save_weights_path, providers=self.providers)
        self.input_cfg = self.session.get_inputs()[0]
        self.input_name = self.input_cfg.name
        self.outputs = self.session.get_outputs()
        self.output_names = [o.name for o in self.outputs]

    def inference(self, input0_data):
        pr = self.session.run(None, {self.input_name : [input0_data]})[0]
        return pr