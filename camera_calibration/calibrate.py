from calibration_api import Camera_Calibration_API
import glob
import numpy as np
import cv2

def calibrate():
    images_path_list = glob.glob("chessboards/*.jpg")
    chessboard = Camera_Calibration_API(pattern_type="chessboard",
                                        pattern_rows=9,
                                        pattern_columns=7,
                                        distance_in_world_units = 10 #lets assume the each square is 10 in some world units
                                    )
    results = chessboard.calibrate_camera(images_path_list)
    intrinsic_matrix = results["intrinsic_matrix"]
    distortion_coeffs = results["distortion_coefficients"]
    print("Saving parameters to file.")
    print(intrinsic_matrix)
    with open("intrinsic_matrix.txt", "w") as file:
        for row in intrinsic_matrix:
            np.savetxt(file, row)
    with open("distortion_coeffs.txt", "w") as file:
        for row in distortion_coeffs:
            np.savetxt(file, row)
    print("calibrating done")

def test_calibration():
    intrinsic_matrix = np.loadtxt("intrinsic_matrix.txt").reshape(3, 3)
    distortion_coeffs = np.loadtxt("distortion_coeffs.txt").reshape(1, 5)
    image = cv2.imread("examples/jetson-2021-07-05-2-00211.jpg")
    # Now undistort the wide-lense image.
    map1, map2 = cv2.initUndistortRectifyMap(intrinsic_matrix, distortion_coeffs, None, intrinsic_matrix, (1280, 720), cv2.CV_16SC2)
    fixed = cv2.remap(
        image,
        map1,
        map2,
        cv2.INTER_LINEAR,
        cv2.BORDER_CONSTANT)
    cv2.imwrite("test_calibration_before.jpg", image)
    cv2.imwrite("test_calibration_after.jpg", fixed)

#calibrate()
test_calibration()

# Birds-eye view.
# pts1 = image resolution
# pts2 = trapezoid of the image to "view from above".
#pts1=np.float32([[0,0],[1919,0],[0,1079],[1919,1079]]) 
#pts2=np.float32([[372,264],[1518,264],[150,907],[1588,770]]) 
#h = cv2.getPerspectiveTransform(pts1, pts2)
# The z-level, from how high we are viewing the object.
#h[2, 2] = 2
#new_image = cv2.warpPerspective(image, h, (1920, 1080), cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR, cv2.BORDER_CONSTANT)
#cv2.imshow("Bird", new_image)
#cv2.waitKey()