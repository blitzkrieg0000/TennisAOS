import logging

from clients.DetectCourtLines.dcl_client import DCLClient
from clients.Redis.redis_client import RedisCacheManager
from libs.DefaultChain.handler import AbstractHandler
from libs.helpers import Converters, EncodeManager, Repositories, Tools

logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)
import numpy as np

#* C3
class CourtLineChain(AbstractHandler):
    def __init__(self) -> None:
        super().__init__()
        self.redisCacheManager = RedisCacheManager()
        self.detectCourtLineClient = DCLClient()
        self.court_warp_matrix = None
        
    def Handle(self, **kwargs):
        # data, BYTE_FRAMES_GENERATOR=None
        data = kwargs.get("data", None)
        BYTE_FRAMES_GENERATOR = kwargs.get("BYTE_FRAMES_GENERATOR", None)

        courtLines = None
        first_frame_bytes = None

        #! 3-DETECT_COURT_LINES (Extract Tennis Court Lines)
        # İlk frame i al ve saha tespiti yapılmamışsa yap
        consumerResponse = next(BYTE_FRAMES_GENERATOR)

        if consumerResponse is not None:
            first_frame_bytes = consumerResponse.data
            frame = Converters.Bytes2Frame(first_frame_bytes)
            
            if frame is None:
                assert "İlk kare doğru alınamadı."
            
            # Override -> Session video ise her videonun ayrı kaynağı olacağından, varsayılan değerlere override yap.
            overrideData = Repositories.getCourtLineBySessionId(self.redisCacheManager, data["session_id"])[0]
            try:
                data["court_line_array"] = overrideData["st_court_line_array"]
                data["sp_stream_id"] = overrideData["sp_stream_id"]
            except Exception as e:
                logging.warning(e)

            if data["court_line_array"] is not None and data["court_line_array"] != "" and not data["force"]:
                courtLines, self.court_warp_matrix = EncodeManager.deserialize(data["court_line_array"])
            
            else:
                courtPointsBytes = b""
                try:
                    courtPointsBytes = self.detectCourtLineClient.extractCourtLines(image=first_frame_bytes)
                except:
                    Repositories.markAsCompleted(self.redisCacheManager, data["process_id"])
                    return None

                courtLines, self.court_warp_matrix = Converters.Bytes2Obj(courtPointsBytes)


            # Tenis çizgilerini postgresqle kaydet
            if courtLines is not None:
                SerializedCourtPoints = EncodeManager.serialize(np.array([courtLines, self.court_warp_matrix]))
                data["court_line_array"] = SerializedCourtPoints
                Repositories.saveCourtLinePoints(self.redisCacheManager, data["stream_id"], data["session_id"], SerializedCourtPoints)
            else:
                return None

                
            canvas = Tools.drawLines(frame, courtLines)
            canvasBytes = Converters.Frame2Bytes(canvas)


        kwargs["courtLines"] = courtLines
        kwargs["court_warp_matrix"] = self.court_warp_matrix
        kwargs["canvas"] = canvas
        kwargs["canvasBytes"] = canvasBytes
        return super().Handle(**kwargs)