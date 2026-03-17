import streamlit as st
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try importing torch
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    st.error("❌ PyTorch not installed. Run: pip install torch torchvision")

# Arduino serial communication
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    st.warning("⚠️ pyserial not installed. Arduino control disabled. Run: pip install pyserial")

# Page config
st.set_page_config(
    page_title="SmartEdge AI - Hardware Control",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .stButton>button {
        background: linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%);
        color: white;
        border-radius: 30px;
        padding: 10px 25px;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 20px rgba(254,107,139,0.3);
    }
    
    .arduino-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        border-left: 5px solid #4ECDC4;
    }
    
    .detection-alert {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 5px;
    }
    
    .led-on {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        border: 2px solid white;
    }
    
    .led-off {
        background: linear-gradient(135deg, #757F9A, #D7DDE8);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
    }
    
    .error-box {
        background: #ff4444;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1 style='font-size: 36px; margin: 0;'>🤖 SmartEdge AI - Hardware Control</h1>
    <p style='font-size: 16px; opacity: 0.9; margin: 5px 0 0 0;'>Object Detection with Arduino LED Control</p>
</div>
""", unsafe_allow_html=True)

# Load YOLOv5 model
@st.cache_resource
def load_model():
    try:
        with st.spinner('🔄 Loading YOLOv5 model...'):
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True, verbose=False)
            return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

# Arduino Controller Class
if SERIAL_AVAILABLE:
    class ArduinoController:
        def __init__(self):
            self.serial_port = None
            self.connected = False
            self.port_name = None
            self.led_state = False
            
        def find_arduino_port(self):
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if any(x in port.description.lower() for x in ['arduino', 'ch340', 'cp210', 'usb serial']):
                    return port.device
            return None
        
        def connect(self, port=None, baudrate=9600):
            try:
                if port is None:
                    port = self.find_arduino_port()
                    if port is None:
                        return False, "❌ No Arduino found!"
                
                self.serial_port = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=2,
                    write_timeout=2
                )
                
                time.sleep(2)  # Wait for Arduino reset
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()
                
                self.connected = True
                self.port_name = port
                
                # Test communication
                success, response = self.send_command("STATUS")
                if success:
                    return True, f"✅ Connected to Arduino on {port}"
                else:
                    return False, "⚠️ Connected but no response from Arduino"
                
            except Exception as e:
                return False, f"❌ Connection failed: {str(e)}"
        
        def disconnect(self):
            if self.serial_port and self.serial_port.is_open:
                # Turn off LED before disconnecting
                self.set_led(False)
                self.serial_port.close()
            
            self.connected = False
            self.port_name = None
            self.led_state = False
        
        def send_command(self, command):
            if not self.connected or not self.serial_port:
                return False, "Not connected"
            
            try:
                # Clear input buffer
                self.serial_port.reset_input_buffer()
                
                # Send command
                self.serial_port.write(f"{command}\n".encode())
                self.serial_port.flush()
                
                # Wait for response
                time.sleep(0.1)
                
                # Read response
                if self.serial_port.in_waiting > 0:
                    response = self.serial_port.readline().decode('utf-8').strip()
                    return True, response
                else:
                    return True, "Command sent"
                    
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def set_led(self, state):
            """Control LED: True=ON, False=OFF"""
            if state == self.led_state:
                return True, f"LED already {'ON' if state else 'OFF'}"
            
            command = "ON" if state else "OFF"
            success, response = self.send_command(command)
            
            if success:
                self.led_state = state
                return True, f"LED turned {'ON' if state else 'OFF'}"
            return False, response
        
        def blink_led(self):
            success, response = self.send_command("BLINK")
            return success, response
        
        def get_status(self):
            success, response = self.send_command("STATUS")
            if success and response.startswith("STATUS:"):
                status = response.split(":")[1]
                self.led_state = (status == "ON")
                return True, f"LED is {status}"
            return False, "Could not get status"

# Initialize session state
if 'arduino' not in st.session_state and SERIAL_AVAILABLE:
    st.session_state.arduino = ArduinoController()
    st.session_state.arduino_connected = False
    st.session_state.last_detection_time = 0
    st.session_state.camera_active = False

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/arduino.png", width=80)
    st.title("⚙️ Control Panel")
    
    if SERIAL_AVAILABLE:
        st.markdown("### 🔌 Arduino Connection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Auto Connect", use_container_width=True):
                with st.spinner("Connecting..."):
                    success, message = st.session_state.arduino.connect()
                    if success:
                        st.session_state.arduino_connected = True
                        st.success(message)
                    else:
                        st.session_state.arduino_connected = False
                        st.error(message)
        
        with col2:
            if st.button("🔌 Disconnect", use_container_width=True):
                st.session_state.arduino.disconnect()
                st.session_state.arduino_connected = False
                st.info("Disconnected")
        
        # Show connection status
        if st.session_state.arduino_connected:
            st.markdown(f"""
            <div class='arduino-card'>
                <h4>✅ Connected</h4>
                <p>Port: {st.session_state.arduino.port_name}</p>
                <p>LED: {'🔴 ON' if st.session_state.arduino.led_state else '⚫ OFF'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Manual LED Control
        if st.session_state.arduino_connected:
            st.markdown("### 💡 Manual Control")
            
            col_led1, col_led2, col_led3 = st.columns(3)
            
            with col_led1:
                if st.button("🔴 ON", use_container_width=True):
                    success, msg = st.session_state.arduino.set_led(True)
                    if success:
                        st.toast("LED ON", icon="✅")
            
            with col_led2:
                if st.button("⚫ OFF", use_container_width=True):
                    success, msg = st.session_state.arduino.set_led(False)
                    if success:
                        st.toast("LED OFF", icon="✅")
            
            with col_led3:
                if st.button("✨ BLINK", use_container_width=True):
                    success, msg = st.session_state.arduino.blink_led()
                    if success:
                        st.toast("Blinking", icon="✨")
    
    st.markdown("---")
    
    # Detection Settings
    st.markdown("### 🎯 Settings")
    confidence_threshold = st.slider("Confidence", 0.0, 1.0, 0.5, 0.05)
    
    selected_classes = st.multiselect(
        "Detect:",
        ['person', 'car', 'dog', 'cat', 'bottle', 'chair', 'book', 'laptop'],
        default=['person', 'car']
    )
    
    led_duration = st.slider("LED ON Duration", 1, 10, 3)

# ============================================
# MAIN - Camera Tab
# ============================================
st.markdown("## 📸 Live Camera Detection")

col1, col2 = st.columns([1, 3])

with col1:
    if not st.session_state.camera_active:
        if st.button("🔴 START CAMERA", type="primary", use_container_width=True):
            st.session_state.camera_active = True
            st.rerun()
    else:
        if st.button("⏹️ STOP CAMERA", use_container_width=True):
            st.session_state.camera_active = False
            # Turn off LED when stopping
            if SERIAL_AVAILABLE and st.session_state.arduino_connected:
                st.session_state.arduino.set_led(False)
            st.rerun()

# LED Status Display
if SERIAL_AVAILABLE and st.session_state.arduino_connected:
    led_placeholder = st.empty()

if st.session_state.camera_active:
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        # Placeholders
        video_placeholder = st.empty()
        stats_placeholder = st.empty()
        
        # Load model
        model = load_model()
        
        if model:
            # Variables
            led_state = False
            last_detection_time = 0
            detection_count = 0
            frame_count = 0
            start_time = time.time()
            
            while st.session_state.camera_active:
                ret, frame = cap.read()
                
                if ret:
                    frame_count += 1
                    
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Run detection
                    with torch.no_grad():
                        results = model(frame_rgb)
                    
                    # Process results
                    detections = results.pandas().xyxy[0]
                    
                    # Calculate FPS
                    fps = frame_count / (time.time() - start_time)
                    
                    # Filter detections
                    current_detection = False
                    if not detections.empty:
                        detections = detections[detections['confidence'] >= confidence_threshold]
                        if selected_classes:
                            detections = detections[detections['name'].isin(selected_classes)]
                        
                        if not detections.empty:
                            current_detection = True
                            detection_count += 1
                            
                            # ============================================
                            # CRITICAL FIX: LED CONTROL LOGIC
                            # ============================================
                            current_time = time.time()
                            
                            # Only turn ON LED if:
                            # 1. Object is detected
                            # 2. LED is currently OFF
                            # 3. Arduino is connected
                            if (SERIAL_AVAILABLE and 
                                st.session_state.arduino_connected and 
                                not led_state):
                                
                                success, _ = st.session_state.arduino.set_led(True)
                                if success:
                                    led_state = True
                                    last_detection_time = current_time
                                    st.success("🔴 LED ON - Object Detected!", icon="🎯")
                            
                            # Draw bounding boxes
                            for _, det in detections.iterrows():
                                x1, y1, x2, y2 = map(int, [det['xmin'], det['ymin'], det['xmax'], det['ymax']])
                                conf = det['confidence']
                                cls = det['name']
                                
                                cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (78, 205, 196), 2)
                                label = f"{cls} {conf:.2f}"
                                cv2.putText(frame_rgb, label, (x1, y1-10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (78, 205, 196), 2)
                    
                    # ============================================
                    # CRITICAL FIX: TURN OFF LED WHEN NO DETECTION
                    # ============================================
                    # Turn OFF LED if:
                    # 1. No object detected in current frame
                    # 2. LED is currently ON
                    # 3. Enough time has passed since last detection
                    if (SERIAL_AVAILABLE and 
                        st.session_state.arduino_connected and 
                        led_state and 
                        not current_detection and 
                        (time.time() - last_detection_time) > led_duration):
                        
                        success, _ = st.session_state.arduino.set_led(False)
                        if success:
                            led_state = False
                            st.info("⚫ LED OFF - No Detection", icon="⚫")
                    
                    # Update LED status display
                    if SERIAL_AVAILABLE and st.session_state.arduino_connected:
                        if led_state:
                            led_placeholder.markdown("""
                            <div class='led-on'>
                                🔴 LED is ON - Object Detected!
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            led_placeholder.markdown("""
                            <div class='led-off'>
                                ⚫ LED is OFF - No Detection
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Display frame
                    video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                    
                    # Statistics
                    with stats_placeholder.container():
                        if current_detection:
                            st.markdown("""
                            <div class='detection-alert'>
                                <h3>🎯 OBJECT DETECTED!</h3>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        col_s1, col_s2, col_s3 = st.columns(3)
                        
                        with col_s1:
                            st.metric("Objects", len(detections) if not detections.empty else 0)
                        with col_s2:
                            st.metric("LED", "ON" if led_state else "OFF")
                        with col_s3:
                            st.metric("FPS", f"{fps:.1f}")
                        
                        if not detections.empty:
                            st.write("**Detected:**")
                            for _, det in detections.iterrows():
                                st.write(f"- {det['name']}: {det['confidence']:.1%}")
            
            cap.release()
    else:
        st.error("❌ Cannot access camera")
else:
    st.info("👆 Click 'START CAMERA' to begin")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🤖 SmartEdge AI - LED turns ON only when objects are detected</p>
</div>
""", unsafe_allow_html=True)