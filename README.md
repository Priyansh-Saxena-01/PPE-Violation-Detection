
# **PPE Violation Detection System**

## **Overview**
This project is an **Object Detection System** designed to detect **Personal Protective Equipment (PPE) violations** at construction sites. Using a **YOLOv7-based model** for real-time inference, it identifies and labels individuals as either "no helmet," "no jacket," "safe," or "unsafe." The system sends **alert emails** when a violation is detected, providing a user-friendly **interface for video uploads or live video streams**.

---

## **Features**
- **Real-time Detection:** Bounding boxes around individuals to classify them based on PPE status.
- **Alerts:** Automatic email notifications for detected violations.
- **User Interface:** Interactive UI for uploading video files or live video feeds.
- **Customizable Labels:** Labels individuals as "safe," "unsafe," "no helmet," or "no jacket" based on detected PPE.

---

## **Getting Started**

### **Prerequisites**
- **Python 3.8+**
- **YOLOv7** pre-trained model and custom-trained weights
- **Roboflow API** for image annotation and data preparation
- **Libraries:** OpenCV, Numpy, PyTorch, and other dependencies (see `requirements.txt`)

### **Installation**
1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/ppe-violation-detection.git
    cd ppe-violation-detection
    ```
2. Install required packages:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up YOLOv7 with pre-trained weights:
   - Download YOLOv7 from the official repository.
   - Use custom-trained weights (`data.pt`) from the project’s training phase.

---

## **Dataset**

- **Data Collection:** Images collected with individuals wearing PPE (helmet, jacket) in various scenarios.
- **Data Annotation:** Images were annotated using **Roboflow** for object detection, creating labels for "no helmet," "no jacket," "safe," and "unsafe."
- **Model Training:** YOLOv7 pre-trained weights were used for transfer learning on this annotated dataset.

---

## **Model Training**

### **Steps:**
1. **Annotation:** Annotated data using **Roboflow**.
2. **Transfer Learning:** Used YOLOv7 pre-trained weights and performed custom training with the annotated dataset.
3. **Weights:** The resulting weights (`data.pt`) are used in the model for inference.

---

## **Usage**

### **1. Running Inference on Video Files**
   - Run the following command to detect PPE violations in a video file:
     ```bash
     python detect.py --source path/to/video.mp4 --weights path/to/data.pt
     ```

### **2. Live Inference**
   - To use live video for inference, connect your webcam or any IP camera:
     ```bash
     python detect.py --source 0 --weights path/to/data.pt
     ```

### **3. Receiving Alerts**
   - Configure email settings in `config.py`.
   - The system automatically sends alerts when violations are detected.

---

## **Project Structure**
- **detect.py**: Main detection script for inference.
- **config.py**: Configuration file for email alerts and settings.
- **requirements.txt**: Required libraries and dependencies.
- **data/**: Folder containing dataset information and model weights.

---

## **Results**
- Achieved **accurate PPE violation detection** with custom-trained YOLOv7 weights.
- **Real-time inference** on video and live feed with robust performance in varied conditions.
- **Alert functionality** integrated to notify supervisors or administrators about detected violations.

---

## **Future Work**
- **Expand PPE Categories:** Additional labels for other PPE types (e.g., gloves, boots).
- **Real-time Data Analytics:** Analysis and logging of PPE compliance trends.
- **Improved Alert System:** SMS or push notifications in addition to email alerts.

---

## **Contributing**
Contributions are welcome! Please fork the repository and submit a pull request.

---

## **License**
This project is licensed under the MIT License. See the `LICENSE` file for more details.

