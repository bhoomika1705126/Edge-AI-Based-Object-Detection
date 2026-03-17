# 🤖 SmartEdge AI - Object Detection with Arduino Control

<div align="center">
  <img src="https://img.icons8.com/fluency/96/arduino.png" width="80"/>
  <img src="https://streamlit.io/images/brand/streamlit-mark-color.png" width="80"/>
  <img src="https://pytorch.org/assets/images/pytorch-logo.png" width="80"/>
</div>

## 📋 Overview

SmartEdge AI is a real-time object detection application that combines computer vision with hardware control. It uses YOLOv5 for object detection and controls an Arduino-connected LED based on detection results.

### ✨ Features

- **Real-time Object Detection** using YOLOv5
- **Arduino LED Control** - LED turns ON when objects are detected
- **Customizable Detection** - Choose which objects to detect
- **Adjustable Confidence** - Set confidence threshold
- **LED Timing Control** - Configure how long LED stays ON
- **Beautiful UI** - Modern Streamlit interface with animations
- **Live Statistics** - FPS, detection count, LED status

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam or camera device
- Arduino board (optional, for LED control)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bhoomika1705126/Edge-AI-Based-Object-Detection.git
   cd Edge-AI-Based-Object-Detection
 # Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

streamlit run app.py
