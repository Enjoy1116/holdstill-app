set +e
cd /mnt/files/v
while ! grep -q CAP2EXIT /home/user/cap2.log 2>/dev/null; do sleep 5; done
cp -n /home/user/out/* /mnt/files/v/out/ 2>/dev/null
export FFMPEG=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p /home/user/work/r /home/user/vout
export WORK=/home/user/work ASSETS=/home/user/out ICON=$PWD/icon.png OUTDIR=/home/user/vout TUTORIAL=$PWD/tutorial.mp4 FONT_BOLD=$PWD/Inter.ttf SKIP=1
step(){ [ -f vout/framey-$1.mp4 ] && { echo SKIP $1; return; }; shift; "$@"; echo "EXIT $? $*"; cp /home/user/vout/*.mp4 vout/ 2>/dev/null; }
step want-blocks python3 vids3.py blocks
step lock-short python3 vids.py lock
step want-dominoes python3 vids3.py dominoes
step green-screen python3 vids2.py green
step how-it-works python3 vids2.py how
step music python3 vids2.py music
step titles-and-drawing python3 vids2.py create
step tutorial python3 vids.py tut
echo ALLDONE
