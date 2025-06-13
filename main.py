import websocket
import time
import json
from config import first_req, first_res, second_res, headers
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
import os
from playsound import playsound
import tkinter as tk
from tkinter import messagebox
from win10toast import ToastNotifier

endpoint = "https://iran-dont-shoot-resource.cognitiveservices.azure.com/"
deployment = "gpt-4.1"
api_version = "2025-01-01-preview"
subscription_key = os.environ.get("API_KEY")

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key
)

initialized = False

# Initialize Windows toast notifier
toaster = ToastNotifier()
# Test notification at startup
try:
    toaster.show_toast("IranAlert", "Windows notifications are enabled!", duration=5, threaded=True)
    print("[Windows notification test sent]")
except Exception as e:
    print(f"[Windows notification test failed]: {e}")

# --- Azure OpenAI API test at startup ---
def test_azure_openai():
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in Hebrew."}
            ],
            max_completion_tokens=50,
            temperature=0.5,
            model=deployment
        )
        print("[Azure OpenAI API test succeeded]")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"[Azure OpenAI API test failed]: {e}")
        exit(1)

test_azure_openai()

def is_first_req(msg_obj):
    try:
        return (
            msg_obj.get("t") == "c" and
            msg_obj.get("d", {}).get("t") == "h" and
            msg_obj.get("d", {}).get("d", {}).get("v") == first_req["d"]["d"]["v"] and
            msg_obj.get("d", {}).get("d", {}).get("h") == first_req["d"]["d"]["h"]
        )
    except Exception:
        return False

def on_message(ws, message):
    global initialized
    print(f"Received: {message}")
    # Handle plain string messages (e.g., '0', '1', etc.)
    if message.strip() in {'0', '1', '2', '3'}:
        print(f"Received control message: {message.strip()}")
        return
    # Handle multiple JSON objects in a single message (concatenated)
    try:
        if message.strip().startswith('{') and message.strip().endswith('}'):  # likely JSON
            # Try to split if multiple JSON objects are concatenated
            objs = []
            idx = 0
            while idx < len(message):
                try:
                    obj, end = json.JSONDecoder().raw_decode(message, idx)
                    objs.append(obj)
                    idx = end
                    # Skip whitespace between objects
                    while idx < len(message) and message[idx].isspace():
                        idx += 1
                except Exception:
                    break
            for msg_obj in objs:
                handle_json_message(ws, msg_obj)
            return
        
    except Exception as e:
        print(f"Failed to parse message as JSON: {e}")
        return

def handle_json_message(ws, msg_obj):
    global initialized
    if is_first_req(msg_obj):
        ws.send(json.dumps(first_res))
        ws.send(json.dumps(second_res))
        print("session is ready!")
        initialized = True
    elif initialized:
        # Handle different message options
        try:
            # Check for the expected structure
            if (
                msg_obj.get("t") == "d" and
                isinstance(msg_obj.get("d", {}).get("b", {}), dict)
            ):
                b = msg_obj["d"]["b"]
                d = b.get("d", {})
                # Print message content if available
                message_content = d.get("messageContent", None)
                if message_content:
                    print(f"Message: {message_content}")
                # Print media links if available
                medias = d.get("medias", {})
                if medias:
                    for media in medias.values():
                        media_content = media.get('mediaContent', '')
                        video_link = media.get('link1', '')
                        thumbnail = media.get('thumbnail', '')
                        print(f"Media: {media_content}")
                        print(f"Video: {video_link}")
                        print(f"Thumbnail: {thumbnail}")
                        # Extract text from mediaContent for further processing
                        if media_content:
                            try:
                                system_prompt = "אתה AI שהולך לקבל דיוווח חדשות מתפרץ. עליך להחליט אם הדיווח רלוונטי ל: הודעה מפיקוד העורף או מגוף צבאי אחר בנושא איום לכיוון ישראל (למשל טילים בליסטים, כטבמים או איומים אחרים שמשמעותיים בזמן הקצר). עליך להגיב בJSON באופן הבא: { isFlagged: True/False, MessageTitle: '...', MessageDescription: '...' } התגובה שלך תכלול רק את ה-JSON."
                                user_prompt = f"New news report: {media_content}"
                                response = client.chat.completions.create(
                                    messages=[
                                        {"role": "system", "content": system_prompt},
                                        {"role": "user", "content": user_prompt}
                                    ],
                                    max_completion_tokens=800,
                                    temperature=1.0,
                                    top_p=1.0,
                                    frequency_penalty=0.0,
                                    presence_penalty=0.0,
                                    model=deployment
                                )
                                ai_content = response.choices[0].message.content
                                print(f"AI Response: {ai_content}")
                                # Remove markdown and whitespace from Azure response
                                ai_content = ai_content.strip()
                                if ai_content.startswith('```json'):
                                    ai_content = ai_content[len('```json'):].strip()
                                if ai_content.startswith('```'):
                                    ai_content = ai_content[len('```'):].strip()
                                if ai_content.endswith('```'):
                                    ai_content = ai_content[:-len('```')].strip()
                                # Fix common JSON issues from AI output
                                ai_content = ai_content.replace("True", "true").replace("False", "false")
                                try:
                                    result = json.loads(ai_content)
                                except Exception as e:
                                    print(f"[JSON ERROR] Could not parse AI response: {ai_content}")
                                    print(f"[JSON ERROR] Exception: {e}")
                                    return
                                if result.get("isFlagged"):
                                    print('CRITICAL NEWS DETECTED!')
                                    try:
                                        playsound('flash.mp3')
                                    except Exception as e:
                                        print(f"Failed to play sound: {e}")
                                    try:
                                        title = result.get("MessageTitle") or "התראה חשובה"
                                        desc = result.get("MessageDescription") or ""
                                        # Show Windows notification first
                                        try:
                                            toaster.show_toast(title, desc, duration=10, threaded=True)
                                            time.sleep(0.5)  # Give time for notification thread to start
                                        except Exception as e:
                                            print(f"Failed to show Windows notification: {e}")
                                        # Then show Tkinter popup
                                        root = tk.Tk()
                                        root.withdraw()
                                        messagebox.showinfo(title, desc)
                                        root.destroy()
                                    except Exception as e:
                                        print(f"Failed to show popup: {e}")
                                else:
                                    print('No critical news detected.')
                            except Exception as e:
                                print(f"Failed to parse AI response for mediaContent: {e}")

                # Print reporter info if available
                reporter = d.get("reporter", {}).get("reporter", {})
                if reporter:
                    print(f"Reporter: {reporter.get('name', '')}")
                    print(f"Reporter Image: {reporter.get('image', '')}")

                if message_content:
                    try:
                        system_prompt = "אתה AI שהולך לקבל דיוווח חדשות מתפרץ. עליך להחליט אם הדיווח רלוונטי ל: הודעה מפיקוד העורף או מגוף צבאי אחר בנושא איום לכיוון ישראל (למשל טילים בליסטים, כטבמים או איומים אחרים שמשמעותיים בזמן הקצר). עליך להגיב בJSON באופן הבא: { isFlagged: True/False, MessageTitle: '...', MessageDescription: '...' } התגובה שלך תכלול רק את ה-JSON."
                        user_prompt = f"New news report: {message_content}"
                        response = client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            max_completion_tokens=800,
                            temperature=1.0,
                            top_p=1.0,
                            frequency_penalty=0.0,
                            presence_penalty=0.0,
                            model=deployment
                        )
                        ai_content = response.choices[0].message.content
                        print(f"AI Response: {ai_content}")
                        ai_content = ai_content.strip()
                        if ai_content.startswith('```json'):
                            ai_content = ai_content[len('```json'):].strip()
                        if ai_content.startswith('```'):
                            ai_content = ai_content[len('```'):].strip()
                        if ai_content.endswith('```'):
                            ai_content = ai_content[:-len('```')].strip()
                        # Fix common JSON issues from AI output
                        ai_content = ai_content.replace("True", "true").replace("False", "false")
                        try:
                            result = json.loads(ai_content)
                        except Exception as e:
                            print(f"[JSON ERROR] Could not parse AI response: {ai_content}")
                            print(f"[JSON ERROR] Exception: {e}")
                            return
                        if result.get("isFlagged"):
                            print('CRITICAL NEWS DETECTED!')
                            try:
                                playsound('flash.mp3')
                            except Exception as e:
                                print(f"Failed to play sound: {e}")
                            try:
                                title = result.get("MessageTitle") or "התראה חשובה"
                                desc = result.get("MessageDescription") or ""
                                # Show Windows notification first
                                try:
                                    toaster.show_toast(title, desc, duration=10, threaded=True)
                                    time.sleep(0.5)  # Give time for notification thread to start
                                except Exception as e:
                                    print(f"Failed to show Windows notification: {e}")
                                # Then show Tkinter popup
                                root = tk.Tk()
                                root.withdraw()
                                messagebox.showinfo(title, desc)
                                root.destroy()
                            except Exception as e:
                                print(f"Failed to show popup: {e}")
                        else:
                            print('No critical news detected.')
                    except Exception as e:
                        print(f"Failed to parse AI response: {e}")
                   
        except Exception as e:
            print(f"Error handling message: {e}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")
    # Attempt to restart the websocket connection from scratch
    try:
        print("[INFO] Attempting to restart websocket connection...")
        # Delay before reconnecting to avoid rapid loops
        time.sleep(3)
        # Re-import and re-run main logic
        import os
        import sys
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        print(f"[ERROR] Failed to restart application: {e}")

def on_open(ws):
    print("### opened ###")

if __name__ == "__main__":
    import threading

    def keepalive(ws_app):
        # Wait until the connection is open before sending keepalives
        while not ws_app.sock or not ws_app.sock.connected:
            time.sleep(1)
        while ws_app.keep_running and ws_app.sock and ws_app.sock.connected:
            time.sleep(30)
            try:
                ws_app.send('0')
                print("Keepalive '0' sent")
            except Exception as e:
                print(f"Failed to send keepalive '0': {e}")
                break

    ws = websocket.WebSocketApp(
        "wss://s-usc1b-nss-2163.firebaseio.com/.ws?v=5&ns=channel-2-news",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        header=[f"{k}: {v}" for k, v in headers.items()]
    )

    ka_thread = threading.Thread(target=keepalive, args=(ws,), daemon=True)
    ka_thread.start()

    ws.run_forever()

    try:
        while True:
            time.sleep(30)
            try:
                ws.send('0')
                print("Keepalive '0' sent")
            except Exception as e:
                print(f"Failed to send keepalive '0': {e}")
                break
    except KeyboardInterrupt:
        print("Interrupted by user.")
