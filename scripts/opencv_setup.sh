# Install OpenCV 2.4.10 on DICE vision PCs
mkdir /disk/scratch/sdp/group7
cd /disk/scratch/sdp/group7
rm -rf opencv-2.4.10*
wget sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.10/opencv-2.4.10.zip
unzip opencv-2.4.10.zip
cd opencv-2.4.10
mkdir build
cd build
cmake -D CMAKE_INSTALL_PREFIX=~/.local ..
sed -i '50d' ../cmake/cl2cpp.cmake
make
make install
# This kills the .brc -- TODO add to path only if necessary
echo 'export PYTHONPATH=$PYTHONPATH:~/.local/lib/python2.6/site-packages' >> ~/.brc
cd /disk/scratch/sdp/group7
rm -rf opencv-2.4.10.zip
cd
