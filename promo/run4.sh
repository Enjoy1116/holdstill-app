# Nightly render of the new "want" scenes (1-6 AM Eastern). Skips ones already in vout.
set +e
cd /mnt/files/v
export FFMPEG=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p /home/user/work/r /home/user/vout
export WORK=/home/user/work ASSETS=/home/user/out ICON=$PWD/icon.png OUTDIR=/home/user/vout TUTORIAL=$PWD/tutorial.mp4 FONT_BOLD=$PWD/Inter.ttf SKIP=1
step(){ [ -f vout/framey-$1.mp4 ] && { echo SKIP $1; return; }; shift; "$@"; echo "EXIT $? $*"; cp /home/user/vout/*.mp4 vout/ 2>/dev/null; }
WORK=$WORK python3 precool.py stack race split rocket
for s in stack race split rocket; do step want-$s python3 vids3.py $s; done
echo ALLDONE
