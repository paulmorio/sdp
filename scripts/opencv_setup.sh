# Install OpenCV 2.4.10 on DICE vision PCs
cd /disk/scratch/sdp
wget sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.10/opencv-2.4.10.zip
unzip opencv-2.4.10.zip
cd opencv-2.4.10
mkdir build
cd build
cmake -D WITH_OPENCL=OFF -D WITH_CUDA=OFF -D BUILD_opencv_gpu=OFF -D BUILD_opencv_gpuarithm=OFF -D BUILD_opencv_gpubgsegm=OFF -D BUILD_opencv_gpucodec=OFF -D BUILD_opencv_gpufeatures2d=OFF -D BUILD_opencv_gpufilters=OFF -D BUILD_opencv_gpuimgproc=OFF -D BUILD_opencv_gpulegacy=OFF -D BUILD_opencv_gpuoptflow=OFF -D BUILD_opencv_gpustereo=OFF -D BUILD_opencv_gpuwarping=OFF -D CMAKE_INSTALL_PREFIX=~/.local ..
make
make install
echo 'export PYTHONPATH=$PYTHONPATH:~/.local/lib/python2.6/site-packages' >> ~/.brc
cd /disk/scratch/sdp
