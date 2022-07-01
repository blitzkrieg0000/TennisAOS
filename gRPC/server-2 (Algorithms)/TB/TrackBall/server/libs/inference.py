import sys
import tritonclient.grpc as grpcclient
import logging
class InferenceManager():
    def __init__(self):
        self.url = "docker-triton-1:8001" # docker-triton-1
        self.client_timeout = None
        self.grpc_compression_algorithm = None
        self.verbose = False
        self.ssl = False
        self.root_certificates = False
        self.private_key=None
        self.root_certificates = None
        self.certificate_chain=None
        self.triton_client = None
        self.connect()

    def connect(self):
        try:
            self.triton_client = grpcclient.InferenceServerClient(
                url=self.url,
                verbose=self.verbose,
                ssl=self.ssl,
                root_certificates=self.root_certificates,
                private_key=self.private_key,
                certificate_chain=self.certificate_chain)
        except Exception as e:
            logging.info("channel creation failed: " + str(e))
            sys.exit()

    def inference(self, input0_data):
        
        model_name = "tracknet_onnx"

        # Infer
        inputs = []
        outputs = []

        inputs.append(grpcclient.InferInput('input_1', [ 9, 360, 640 ], "FP32"))

        # Create the data for the two input tensors. Initialize the first
        # to unique integers and the second to all ones.
        #input0_data = np.expand_dims(input0_data, axis=0)

        # Initialize the data
        inputs[0].set_data_from_numpy(input0_data)
        outputs.append(grpcclient.InferRequestedOutput('activation_18'))

        # # Test with outputs
        # results = self.triton_client.infer(model_name=model_name, inputs=inputs, outputs=outputs,
        #     client_timeout=self.client_timeout,
        #     headers={'test': '1'},
        #     compression_algorithm=self.grpc_compression_algorithm)

        # Test with no outputs
        results = self.triton_client.infer(model_name=model_name, inputs=inputs, outputs=None,
            compression_algorithm=self.grpc_compression_algorithm)

        if self.verbose:
            statistics = self.triton_client.get_inference_statistics(model_name=model_name)
            logging.info(statistics)
            if len(statistics.model_stats) != 1:
                logging.info("FAILED: Inference Statistics")
                sys.exit(1)

        # Get the output arrays from the results
        output0_data = results.as_numpy('activation_18')
        return output0_data