import cv2
import numpy as np


class EdgeDetector():
    def __init__(self) -> None:
        self.__EdgeDetectionMethods = {
            "Robert": self.Robert, "Sobel":self.Sobel, "Laplace":self.Laplace, "Prewitt":self.Prewitt, "Canny":self.Canny
        }
    
    def Extract(self, frame, method_name):
        if method_name is None:
            return frame
            
        if method_name not in self.__EdgeDetectionMethods.keys():
            raise AssertionError(f"Geçerli metot isimleri: {list(self.__EdgeDetectionMethods.keys())}")
        return self.__EdgeDetectionMethods.get(method_name, None)(frame)

    def PreProcess(func):
        def wrapper(self, *args, **kwargs):
            img = args[0].copy()
            return func(self, img)

        return wrapper

    @PreProcess
    def Sobel(self, image:np.ndarray):

        # Dikey Çizgiler
        grad_x = cv2.Sobel(image, cv2.CV_16S, 1, 0, ksize=3, scale=1, delta=0, borderType=cv2.BORDER_DEFAULT)

        # Yatay Çizgiler
        grad_y = cv2.Sobel(image, cv2.CV_16S, 0, 1, ksize=3, scale=1, delta=0, borderType=cv2.BORDER_DEFAULT)
        
        # Normalize Et -> 0 ile 255 arasında değerlere sığdır.
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)

        # İki görüntüyü blendle
        grad = cv2.addWeighted(abs_grad_x, 0.7, abs_grad_y, 0.7, 0)

        return grad


    @PreProcess
    def Robert(self, image:np.ndarray):
        gray = image.astype('float64')
        gray /= 255.0

        roberts_cross_r = np.array( 
                                    [
                                        [1, 0 ],
                                        [0, -1 ]
                                    ] 
                                )
        
        roberts_cross_l = np.array( 
                                    [
                                        [ 0, 1 ],
                                        [-1, 0 ]
                                    ] 
                                )


        line_r = cv2.filter2D(gray, -1, roberts_cross_r)
        line_l = cv2.filter2D(gray, -1, roberts_cross_l)


        # İki görüntüyü blendle
        grad = np.sqrt(np.square(line_r) + np.square(line_l))
        grad = grad*255
        grad = cv2.convertScaleAbs(grad)

        return grad


    @PreProcess
    def Prewitt(self, image:np.ndarray):
        kernelx = np.array([[1,1,1],[0,0,0],[-1,-1,-1]])
        kernely = np.array([[-1,0,1],[-1,0,1],[-1,0,1]])
        img_prewittx = cv2.filter2D(image, -1, kernelx)
        img_prewitty = cv2.filter2D(image, -1, kernely)

        # İki görüntüyü blendle
        grad = cv2.addWeighted(img_prewittx, 0.5, img_prewitty, 0.5, 0)

        return grad


    @PreProcess
    def Canny(self, image:np.ndarray):
        # Gürültüyü azaltmak için
        result = cv2.Canny(image, 50, 200)
        return result


    @PreProcess
    def Laplace(self, image:np.ndarray):
        dst = cv2.Laplacian(image, cv2.CV_16S, ksize=3)
        # converting back to uint8
        result = cv2.convertScaleAbs(dst)
        return result
