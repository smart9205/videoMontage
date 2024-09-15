from fer import FER
import cv2
import imutils
import matplotlib.pyplot as plt  
import numpy as np  
from PIL import Image
import time

from moviepy.editor import *
from moviepy.config import change_settings  
from moviepy.video.compositing.transitions import crossfadein, crossfadeout  
import math
import mediapipe as mp
from aiohttp import web
import argparse
import logging
import ssl
import aiohttp_jinja2
import jinja2
from tempfile import NamedTemporaryFile
import datetime


# change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})  


ROOT = os.path.dirname(__file__)
app = web.Application()




x = []
y = []
eval = [0]
clips = []

mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)


def process_clip(interval_length):
    max_value = max(eval)
    max_index = eval.index(max_value)

    print("max-----------")
    print(max_index)
    print(max_value)
    s=0
    for j in range(interval_length):
        if (max_index-j)>=0:
            eval[max_index-j] = 0
        if (max_index+j+1)<len(eval):
            s += y[max_index+j]     
            eval[max_index+j+1] = s
    return max_index


async def run(request):
    data = await request.json()  # get data from POST request  
    path = data.get('path')  # get 'path' from data  

    print("called....")
    print(path)

    
    start_T = time.time()

    emotion_detector = FER(mtcnn=True)
    clipSource = VideoFileClip(path)
    audioclip = AudioFileClip("img/audio_2.mp3")
    video = cv2.VideoCapture(path)
    fps = video.get(cv2.CAP_PROP_FPS)
    cnt = 0
    clipTime = 5
    interval_length = int(fps*clipTime)
    

    while True:
        ret, frame = video.read()
        cnt +=1
        if ret:
                frame = imutils.resize(frame, width=640)
                value = 0
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detection.process(image_rgb)
                if results.detections:
                    for detection in results.detections:
                        bboxC = detection.location_data.relative_bounding_box
                        ih, iw, _ = frame.shape
                        bbox = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)
                        margin = int(bboxC.height * iw/6)  
                        bbox = max(0, bbox[0] - margin), max(0, bbox[1] - int(margin*1.45)), min(iw, bbox[2] + 2*margin), min(ih, bbox[3] + 2*margin)
                        face = frame[bbox[1]:bbox[1]+bbox[3], bbox[0]:bbox[0]+bbox[2]]
                        face = imutils.resize(face, height=96)
                        analysis = emotion_detector.detect_emotions(face)
                        if (analysis):
                            value = analysis[0]['emotions']['happy'] * 100
                            if value < 80:
                                value = 0
                timestamp = video.get(cv2.CAP_PROP_POS_MSEC)/1000
                x.append(timestamp)
                y.append(value)
        else:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    nframes = len(y)
    x.insert(0, 0)
    for i in range(nframes):
        if i < interval_length:
            eval.append(eval[-1] + y[i])
        else:
            eval.append(eval[-1] + y[i] - y[i-interval_length])

    for i in range(3):
        ind = process_clip(interval_length)
        if ind >= len(x):
            ind = len(x)-1
        end_time = math.ceil(x[ind])
        start_time = max(0, (end_time-clipTime))
        print("startendtime-----------------------------------")
        print(start_time)
        print(end_time)
        clip = clipSource.subclip(start_time, end_time).fx(crossfadein, 1).fx(crossfadeout, 1)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips)

    if audioclip.duration > final_clip.duration:  
        audioclip = audioclip.subclip(0, final_clip.duration)  
    elif audioclip.duration < final_clip.duration:  
        audioclip = audioclip.fx(vfx.loop, duration=final_clip.duration)  
        
    final_clip = final_clip.set_audio(audioclip)

    logo = (ImageClip("img/logo2.png")  
            .set_duration(final_clip.duration)  # So logo duration matches main video duration  
            .resize(height=50)  # Adjust the height (in pixels)  
            .margin(right=8, top=8, opacity=0)  # (optional) logo margin  
            .set_pos(("right", "top")))  # Position: top-right  
    
    happy_mark = (ImageClip("img/happy.png")  
            .set_duration(final_clip.duration)  # So logo duration matches main video duration  
            .resize(height=50)  # Adjust the height (in pixels)  
            .margin(right=8, top=8, opacity=0)  # (optional) logo margin  
            .set_pos(("right", "top")))  # Position: top-right  

    # Create text  
    # txt_clip = (TextClip("Smile", fontsize=24, color='white')  
    #              .set_duration(final_clip.duration)  
    #              .set_pos('center'))  


    final_clip = CompositeVideoClip([final_clip, logo, happy_mark])  

    now = datetime.datetime.now()  
    
    # Format the current date and time as a string  
    filename = now.strftime("%Y%m%d_%H%M%S.mp4")  

    final_clip.write_videofile(f"static/result/{filename}")
    
    tt = time.time() - start_T
    print("time------")
    print(tt)

    x.pop(0)
    plt.figure(figsize=(10, 6))  
    plt.xlabel('Time (s)')  
    plt.ylabel('Happy Value')  
    plt.plot(x, y, 'o')
    plt.plot(x, y, '-', label='Line')
    plt.title('Graph of Value over Time')  
    # plt.show()
    plt.savefig('graph.png')  
    return web.json_response({  
        'video_url': '/static/result/' + filename 
    })  


async def upload_video(request):
    print("---uploading")
    global video_url
    global processed
    video_url = ""
    reader = await request.multipart()
    file = await reader.next()
    filestr = await file.read()
    with NamedTemporaryFile(delete=False, suffix=".mp4") as temp:
        temp.write(filestr)
        temp.flush()
        print("uploaded---")
        video_url = temp.name
    
    print("---------*****------------")
    print(video_url)
    processed = False
    return web.Response(text=video_url)


aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
@aiohttp_jinja2.template('index.html')
async def index(request):
    alert_msg = ""
    print("initialized.....")
    return {'alert_msg': alert_msg}

async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Montage demo"
    )
    parser.add_argument("--cert-file", default="", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", default="", help="SSL key file (for HTTPS)")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8001, help="Port for HTTP server (default: 8080)"
    )
    parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.cert_file and args.key_file:
        cert_file = os.path.join(os.getcwd(), args.cert_file)
        key_file = os.path.join(os.getcwd(), args.key_file)
        
        # ssl_context = ssl.SSLContext()
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        ssl_context.load_cert_chain(cert_file, key_file)
    else:
        ssl_context = None

    app.router.add_static('/static/', path='static', name='static')
    app.router.add_get("/client.js", javascript)
    app.router.add_post('/upload', upload_video)
    app.router.add_post('/run', run)
    app.router.add_get('/', index)
    web.run_app(
        app, access_log=None, host=args.host, port=args.port, ssl_context=ssl_context
    )