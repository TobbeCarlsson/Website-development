#!/usr/bin/env python
from flask import Flask, render_template, Response,request
from flask_cors import CORS

import time
import random
import base64
import json
import threading
import wave
import math
import os
# MP3 streaming:
import subprocess
import select
import re

app = Flask(__name__)
cors = CORS(app)
# Copied from https://stackoverflow.com/questions/51079338/audio-livestreaming-with-python-flask
def generate_wav_header(sampleRate, bitsPerSample, channels):
    datasize = 2000*10**6
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o

class DialogueEncoder(json.JSONEncoder):
    def default(self, obj):
        d = {}
        d["closed"] = obj.closed
        d["end_of_speech_timestamp"] = obj.end_of_speech_timestamp
        d["timestamp"] = obj.timestamp
        d["state"] = obj.state
        d["length"] = obj.length
        d["message"] = obj.message
        d["robot_lines"] = obj.robot_lines
        d["user_lines"]= obj.user_lines
        d["dialogue_hash"] = obj.dialogue_hash
        d["length"] = obj.length
        d["evaluations"] = obj.evaluations
        d["can_end"] = obj.can_end
        d["audio_identifiers"] = obj.audio_identifiers
        d["secret_code"] = obj.secret_code
        return d

class DialogueDecoder(json.JSONDecoder):
   def decode(self, s):
        d = json.loads(s)
        dialogue = Dialogue()
        dialogue.closed = d["closed"]
        dialogue.end_of_speech_timestamp = d["end_of_speech_timestamp"]
        dialogue.timestamp = d["timestamp"]
        dialogue.state = d["state"]
        dialogue.length = d["length"]
        dialogue.message = d["message"]
        dialogue.robot_lines = d["robot_lines"]
        dialogue.user_lines = d["user_lines"]
        dialogue.dialogue_hash = d["dialogue_hash"]
        dialogue.length = d["length"]
        dialogue.evaluations = d["evaluations"]
        dialogue.can_end = d["can_end"]
        dialogue.audio_identifiers = d["audio_identifiers"]
        dialogue.secret_code = d["secret_code"]
        return dialogue

def update_dialogue_from_JSON(dialogue, s):
    d = json.loads(s)
    dialogue.closed = d["closed"]
    dialogue.end_of_speech_timestamp = d["end_of_speech_timestamp"]
    dialogue.timestamp = d["timestamp"]
    dialogue.state = d["state"]
    dialogue.length = d["length"]
    dialogue.message = d["message"]
    dialogue.robot_lines = d["robot_lines"]
    dialogue.user_lines = d["user_lines"]
    dialogue.dialogue_hash = d["dialogue_hash"]
    dialogue.length = d["length"]
    dialogue.evaluations = d["evaluations"]
    dialogue.can_end = d["can_end"]
    dialogue.audio_identifiers = d["audio_identifiers"]
    dialogue.secret_code = d["secret_code"]

def update_dialogue_from_file(dialogue, close_timed_out = True):
    if close_timed_out:
        close_timed_out_dialogues_once()
    file_contents = open(f"dialogues/{dialogue.dialogue_hash}", 'r').read()
    update_dialogue_from_JSON(dialogue, file_contents)
    return dialogue

def save_dialogue_state_to_file(dialogue, close_timed_out = True):
    if close_timed_out:
        close_timed_out_dialogues_once()
    file_to_which_to_write = open(f"dialogues/{dialogue.dialogue_hash}", 'w')
    file_to_which_to_write.write(json.dumps(dialogue, cls = DialogueEncoder))

def load_dialogue_from_file(dialogue_hash, close_timed_out = True):
    if close_timed_out:
        close_timed_out_dialogues_once()
    file_from_which_to_read = open(f"dialogues/{dialogue_hash}", 'r')
    return json.loads(file_from_which_to_read.read(), cls = DialogueDecoder)

def audio_file_generator(audio_identifier, dialogue):
    try:
        file_object = open(f"audio/dialogue/{audio_identifier}.mp3", 'r')
        # File definitely exists. 
        # TODO: -re? That's supposed to stream the file in real time but seems to break browsers.
        poll = select.poll()
        pipe = subprocess.Popen(f'ffmpeg -i audio/dialogue/{audio_identifier}.mp3 -ar 16000 -ac 1 -f mp3 pipe:'.split(), stdout = subprocess.PIPE)
        poll.register(pipe.stdout, select.POLLIN)
        go_around_counter = 1
        while True:
            go_around_counter += 1
            if pipe.returncode is not None:
                poll.unregister(pipe.stdout)
                pipe.kill()
                break
            else:
                data_to_yield = pipe.stdout.readline()
                yield data_to_yield
        file_object.close()
    except FileNotFoundError:
        pass

class Dialogue():
    closed = False
    end_of_speech_timestamp = -1
    speaking_audio_file = None
    idle_audio_file = None
    audio_stream = None
    timestamp = None
    state = "ongoing"
    length = None
    message = ""
    robot_lines = []
    user_lines = []
    dialogue_hash = None
    length = None
    can_end = False
    secret_code = None

    evaluations = {}
    audio_identifiers = {}

    def set_message(self, message):
        self.message = message

    def get_state(self):
        return self.state

    def is_ongoing(self):
        return self.get_state() == "ongoing"

    def is_evaluating(self):
        return self.get_state() == "evaluating"

    def is_over(self):
        return self.get_state() == "over"

    def is_talking(self):
        return self.end_of_speech_timestamp >= time.time()

    def get_unrated_robot_lines(self):
        return [l for l in self.robot_lines if "rating" not in l.keys() and l["should_be_rated"]]

    def get_unrated_robot_line_count(self):
        return len(get_unrated_robot_lines())
        
    # def generate_audio_chunk_and_get_identifier(self, length_milliseconds):
    #     audio_identifier = generate_random_hash(length = 16).decode("utf-8")
    #     output_file_name = f"audio/dialogue/{audio_identifier}.mp3"
    #     # Ask FFMPEG to cut out a random chunk of the simlish file and put it there.
    #     really_look_up_file_length = False
    #     file_length_milliseconds = None
    #     if really_look_up_file_length:
    #         duration_regex = r'Duration: (\d\d):(\d\d):(\d\d)\.(\d\d)'
    #         subprocess_output = subprocess.run("ffmpeg -i audio/simlish.mp3".split(), stdout = subprocess.PIPE, stderr = subprocess.STDOUT).stdout
    #         duration_regex_results = re.search(duration_regex, str(subprocess_output))
    #         hours = int(duration_regex_results.group(1))        
    #         minutes = int(duration_regex_results.group(2))        
    #         seconds = int(duration_regex_results.group(3))        
    #         hundreds = int(duration_regex_results.group(4))
    #     else:
    #         hours = 0       
    #         minutes = 4      
    #         seconds = 23        
    #         hundreds = 99
            
    #     file_length_milliseconds = 10 * hundreds + 1000 * seconds + (60 * 1000) * minutes + (60 * 60 * 1000) * hours
    #     start_maximum = file_length_milliseconds - length_milliseconds

    #     random_start_point_roll = random.randint(0, start_maximum)
    #     random_start_point_roll_seconds = random_start_point_roll / 1000
    #     clip_length_seconds = length_milliseconds / 1000
    #     ffmpeg_command = f"ffmpeg -i audio/simlish.mp3 -ss {random_start_point_roll_seconds} -t {clip_length_seconds} -ar 16000 -ac 1 -f wav audio/dialogue/{audio_identifier}.mp3"
    #     # print(f"Debug: FFMPEG command to cut simlish into chunks is {ffmpeg_command}.")

    #     time_before_cutting = time.time()
    #     subprocess.run(ffmpeg_command.split())
    #     time_after_cutting = time.time()

    #     # print(f"Debug: cutting and creating {audio_identifier}.mp3 took {time_after_cutting - time_after_cutting} seconds.")

    #     self.audio_identifiers[audio_identifier] = time_after_cutting + length_milliseconds / 1000
    #     return audio_identifier

    def __init__(self):
        self.robot_lines = []
        self.user_lines = []
        self.timestamp = time.time()
        self.dialogue_hash = generate_random_hash().decode("utf-8")
        self.length = random.randint(3, 7)
        self.secret_code = generate_random_hash(length = 12).decode("utf-8")

    def add_robot_line(self, robot_line, options, should_be_rated = True):
        self.timestamp = time.time()
        index = 1 + len(self.user_lines) + len(self.robot_lines)
        self.timestamp = time.time()
        characters_in_speech = len(robot_line)
        delay_milliseconds = 100 + 35 * characters_in_speech
        #audio_identifier = self.generate_audio_chunk_and_get_identifier(delay_milliseconds)
        self.end_of_speech_timestamp = self.timestamp + 0.35 * characters_in_speech
        self.robot_lines.append({"index": index, "speaker": "robot", "time": self.timestamp, "line": robot_line, "options": options, "delay": delay_milliseconds, "should_be_rated": should_be_rated, "audio": "audio_identifier"})


    def add_user_line(self, user_line):
        self.timestamp = time.time() # Intentional: if someone tried to talk, the conversation shouldn't time out even if it fails because it wasn't an option

        if not self.is_ongoing():
            raise ValueError(f"Can't add user lines while dialogue is {self.state}.")
        if self.robot_lines[-1]["options"] != [] and user_line not in self.robot_lines[-1]["options"]:
            raise ValueError("Not in the options (" + ",".join(self.robot_lines[-1]["options"]) + ")!")

        index = 1 + len(self.user_lines) + len(self.robot_lines)
        self.user_lines.append({"index": index, "speaker": "user", "time": self.timestamp, "line": user_line})

        if len(self.user_lines) + len(self.robot_lines) >= self.length:
            self.state = "evaluating"
            unrated_lines = self.get_unrated_robot_lines()
            remaining_line_indices = ", ".join([str(l["index"]) for l in unrated_lines])
            self.set_message(f"Still need to rate lines {remaining_line_indices} ({len(unrated_lines)} lines).")
        else:
            self.set_message("Please send response.")

    def add_evaluation(self, index, rating):
        if not self.is_evaluating():
            raise ValueError(f"Can't evaluate while dialogue is {self.state}.")
            
        rating_count = 0

        for line in [l for l in self.robot_lines if l["index"] == index]:
            line["rating"] = rating
            rating_count += 1

        if rating_count < 1:
            raise ValueError(f"Line {index} is not a robot line.")

        unrated_lines = self.get_unrated_robot_lines()

        if len(unrated_lines) == 0:
            self.can_end = True
            self.set_message("No lines remain to rate. Send command to end dialogue when you are done.")
        else:
            if len(unrated_lines) > 1:
                remaining_line_indices = ", ".join([str(l["index"]) for l in unrated_lines])
                self.set_message(f"Still need to rate lines {remaining_line_indices} ({len(unrated_lines)} lines).")
            else:
                remaining_line_index = unrated_lines[0]["index"]
                self.set_message(f"Still need to rate line {remaining_line_index} (1 line).")

    def end_dialogue(self):
        if self.is_over():
            raise ValueError("Dialogue has already ended.")
        elif self.can_end:
            self.state = "over"
            self.timestamp = time.time()
            self.set_message(f"Dialogue was ended at time {self.timestamp}.")
        elif self.is_evaluating():
            evaluations_left = self.get_unrated_robot_line_count()
            raise ValueError("Dialogue can't be ended: {evaluations_left} evaluations left.")
        elif self.is_ongoing():
            raise ValueError("Dialogue can't be ended: still talking.")
        else:
            raise ValueError("Dialogue can't be ended: unknown reason.")
    

    def get_dialogue_history(self):
        return_list = self.robot_lines + self.user_lines
        return_list = sorted(return_list, key = lambda e: e["time"])
        return return_list

    def to_public_json(self):
        d = {}
        d["hash"] = self.dialogue_hash
        d["history"] = self.get_dialogue_history()
        d["state"] = self.get_state()
        d["message"] = self.message
        d["can_end"] = self.can_end
        d["secret_code"] = self.secret_code if self.get_state() == "over" else "Not revealed yet."
        return d

    def has_timed_out(self, timeout_by_state = {"ongoing": 300, "evaluating": 300, "over": 30}):
        timeout = timeout_by_state[self.get_state()]
        time_since_timestamp = time.time() - self.timestamp
        return time_since_timestamp > timeout

    def close(self):
        self.closed = True
        if self.audio_file is not None:
            self.audio_file.close()
        if self.audio_stream is not None:
            self.audio_stream.stop_stream()
            self.audio_stream.close()

    def video_generator(self, frame_rate = 24):
        time_of_last_frame = time.time()
        while not self.closed:
            update_dialogue_from_file(self)
            time_left = 1 / frame_rate + time.time() - time_of_last_frame
            if time_left > 0:
                time.sleep(time_left)
            yield(b"".join([b'--frame\r\nContent-Type: image/jpeg\r\n\r\n', self.get_video_frame(), b'\r\n']))

    def get_video_frame(self):
        if self.is_talking():
            return random.choice(talking_frames)
        else:
            return random.choice(idle_frames)
            

# ongoing_dialogues = {} <- Now handled with files to synchronise multiple threads.
talking_frames = [open(f, 'rb').read() for f in ["talk1.jpeg", "talk2.jpeg", "talk3.jpeg"]]
idle_frames = [open(f, 'rb').read() for f in ["idle1.jpeg", "idle2.jpeg", "idle3.jpeg"]]

caesar_lines = [l.strip() for l in open("caesar.txt").read().split("\n")]

def generate_random_hash(length = 64):
    random_bytes = bytes([random.randint(0, 255) for i in range(length)])
    return base64.urlsafe_b64encode(random_bytes)

def generate_response(return_options):
    line = ""
    options = []
    if return_options:
        yes_no_questions = ["Do you call all dogs 'puppies'?", "Do you like piña coladas?", "Do you ever pick your nose when you think nobody is watching?", "Have you ever worn underwear two days in a row?", "Have you ever lied about having seen a movie?", "Do you ever talk to yourself?", "Do you ever talk to your pets?", "Do you sing silly songs to your pets?", "Have you ever hidden a snack so that nobody else would find it and eat it first?", "Do you think you would be a good ninja?", "Do you ever narrate your life inside your head as if you were in a movie?", "Do you still believe in Santa?", "Do you sing in the shower?", "Do you talk in your sleep?", "Have you ever had a crush on a cartoon character?", "Would you ever date someone who looked exactly like a relative?", "If a future version of you time traveled to this moment, do you think the two of you would get along?", "Do you have an embarrassing nickname?", "Does what happens in Vegas really stay in Vegas?", "Have you ever lied about your birthday to get a free dessert?", "Have you ever ordered takeout to avoid doing dishes?", "Have you ever caught yourself telling someone 'when I was your age…'", "Have you ever cheated at a board game?", "Do you typically learn the naughty words in other languages before learning regular words?", "Are you secretly an owl inside a human robot?", "Have you ever made a ridiculous impulse purchase?", "Have you ever told an outrageous lie to a child?", "Have you ever stolen from a kid’s Halloween candy stash?", "If you learned that I was secretly a spy, would you be surprised?"]
        line = random.choice(yes_no_questions)
        options = ["Yes", "No"]
        if random.random() < .5:
            options.append("Maybe")
        if random.random() < .5:
            options.append("What the hell?")
    else:
        global caesar_lines
        line = random.choice(caesar_lines)
    
    return (line, options)

@app.route('/')
def index():
    new_dialogue_object = new_dialogue(return_response = False)
    return render_template('index.html', identifier = new_dialogue_object.dialogue_hash, dialogue = json.dumps(new_dialogue_object.to_public_json()))

@app.route('/new_dialogue')
def new_dialogue(return_response = True):
    dialogue = Dialogue()
    dialogue.add_robot_line("Hello! Do you want to talk to me?", ["Yes", "No"], should_be_rated = False)
    save_dialogue_state_to_file(dialogue)
    if return_response:
        return Response(json.dumps(dialogue.to_public_json()), 200, mimetype = "application/json")
    else:
        return dialogue

@app.route('/end_dialogue/<identifier>', methods = ["POST"])
def end_dialogue(identifier):
    dialogue = None

    try:
        dialogue = load_dialogue_from_file(identifier)
    except FileNotFoundError as fnfe:
        dialogue = None

    print(dialogue)
    if dialogue is None:
        return Response('{"error": "No such dialogue."}', 404, mimetype = "application/json")
    else:
        try:
            dialogue.end_dialogue()
            save_dialogue_state_to_file(dialogue)
            return Response(json.dumps(dialogue.to_public_json()), 200, mimetype = "application/json")
        except ValueError as v:
                return Response(f'{"error": "{v}"}', 406, mimetype = "application/json")
    
@app.route('/existing_dialogue/<identifier>', methods=["POST"])
def existing_dialogue(identifier):
    dialogue = None

    try:
        dialogue = load_dialogue_from_file(identifier)
    except FileNotFoundError as fnfe:
        dialogue = None


    if dialogue is None:
        return Response('{"error": "No such dialogue."}', 404, mimetype = "application/json")
    else:
        user_json = None
        try:
            user_json = request.get_json(force = True)
        except Exception:
            pass

        if user_json is None:
            return Response('{"error": "No JSON header given."}', 406, mimetype = "application/json")

        if dialogue.is_ongoing():
            try:
                user_text = user_json["response"]
            except KeyError:
                return Response('{"error": "No response (should be text under the key of \\\"response\\\") in JSON data."}', 406, mimetype = "application/json")

            try:
                dialogue.add_user_line(user_text)
            except ValueError as v:
                return Response('{"error": ' + v + '}', 406, mimetype = "application/json")
                
            line, options = generate_response(random.random() < .25)
            dialogue.add_robot_line(line, options)
            save_dialogue_state_to_file(dialogue)
            return Response(json.dumps(dialogue.to_public_json()), 200, mimetype = "application/json")
        elif dialogue.is_evaluating():          
            try:
                user_rating = int(user_json["rating"])
            except KeyError:
                return Response('{"error": "No rating (should be an integer under the key of \\\"rating\\\") in JSON data."}', 406, mimetype = "application/json")          
            try:
                index_being_rated = int(user_json["index"])
            except KeyError:
                return Response('{"error": "No index being rated (should be an integer under the key of \\\"index\\\") in JSON data."}', 406, mimetype = "application/json")

            try:
                dialogue.add_evaluation(index_being_rated, user_rating)
            except ValueError as v:
                return Response('{"error": ' + v + '}', 406, mimetype = "application/json")

            save_dialogue_state_to_file(dialogue)
            return Response(json.dumps(dialogue.to_public_json()), 200, mimetype = "application/json")
        elif dialogue.is_done():
            return Response(json.dumps(dialogue.to_public_json()), 200, mimetype = "application/json")

def video_gen(identifier):
    video_capture = cv2.VideoCapture("morbius.mp4")
    frame_rate = video_capture.get(5)
    frame_interval = 1 / frame_rate
    time_of_previous = -1
    successful = True
    frame_index = 1
    while successful:
        successful, frame = video_capture.read()

        if (time.time() - time_of_previous) < frame_interval:
            time.sleep(frame_interval - (time.time() - time_of_previous))

        if successful:
            encoding_successful, frame_as_jpeg = cv2.imencode(".jpeg", frame)
            jpeg_bytes = frame_as_jpeg.tobytes()
            time_of_previous = time.time()
            frame_index += 1
            yield(b"".join([b'--frame\r\nContent-Type: image/jpeg\r\n\r\n', jpeg_bytes, b'\r\n']))

@app.route('/video_feed/<identifier>')
def video_feed(identifier):
    dialogue = None
    try:
        dialogue = load_dialogue_from_file(identifier)
    except FileNotFoundError:
        dialogue = None

    if dialogue is None:
        return Response('{"error": "No such dialogue."}', 404, mimetype = "application/json")
    else:
        return Response(dialogue.video_generator(), mimetype = 'multipart/x-mixed-replace; boundary=frame')

@app.route('/audio_feed/<identifier>/<audio_identifier>.mp3')
def audio_feed_line(identifier, audio_identifier):
    dialogue = None
    try:
        dialogue = load_dialogue_from_file(identifier)
    except FileNotFoundError:
        dialogue = None

    if dialogue is None:
        return Response('{"error": "No such dialogue."}', 404, mimetype = "application/json")
    else:
        if audio_identifier not in dialogue.audio_identifiers:
            return Response('{"error": "Given dialogue exists, but has no such audio clip."}', 404, mimetype = "application/json")
        else:
            return Response(audio_file_generator(audio_identifier, dialogue), headers = {'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': 0}, mimetype = 'audio/wav')

def close_timed_out_dialogues_once():
    files_in_dialogue_directory = [f for f in os.listdir("dialogues/") if os.path.isfile(os.path.join("dialogues", f))]
    loaded_dialogues = [load_dialogue_from_file(f, close_timed_out = False) for f in files_in_dialogue_directory]
    timed_out_hashes = [d.dialogue_hash for d in loaded_dialogues if d.has_timed_out()]
    for h in timed_out_hashes:
        print(f"Killing dialogue {h} because of inactivity!")
        dialogue_object = load_dialogue_from_file(h, close_timed_out = False)

        for audio_identifier in dialogue_object.audio_identifiers.keys():
            try:
                os.remove(f"audio/dialogue/{audio_identifier}.mp3")
            except FileNotFoundError:
                pass
        try:
            os.remove(f"dialogues/{h}")
        except FileNotFoundError:
            pass
