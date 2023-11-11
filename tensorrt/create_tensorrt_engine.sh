CONVERTER_PATH="/usr/local/stairway-jones/tensorrt/tensorrt_converter"
YOLO_PATH="/usr/local/stairway-jones/tensorrt/yolov5-4.0"
OUTPUT_PATH="/usr/local/stairway-jones/tensorrt/output"
TRITON_PATH="/usr/local/stairway-jones/triton"
sudo /bin/systemctl stop triton.service
cp tensorrt/latest_weights/weights.pt $YOLO_PATH
cd $YOLO_PATH
python3 gen_wts.py
mv weights.wts $CONVERTER_PATH/yolov5s.wts
cd $CONVERTER_PATH
rm -fr build
mkdir build;cd build;cmake ..;make
./yolov5 -s
mkdir -p $OUTPUT_PATH
cp $CONVERTER_PATH/build/yolov5s.engine $OUTPUT_PATH/model.plan
cp $CONVERTER_PATH/build/libmyplugins.so $OUTPUT_PATH
cp $OUTPUT_PATH/model.plan $TRITON_PATH/models/yolov5/1/
cp $OUTPUT_PATH/libmyplugins.so $TRITON_PATH/plugins/
sudo /bin/systemctl start triton.service