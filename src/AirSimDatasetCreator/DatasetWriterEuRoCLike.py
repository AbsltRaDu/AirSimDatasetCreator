from pathlib import Path
import csv

import cv2
import numpy as np

class EuRoCDatasetWriter:
    '''
    Создает структуру датасета, похожую на EuRoC MAV.
    '''

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

        # Камеры 
        self.cam0_dir = self.root_dir / "mav0" / "cam0" / "data"
        self.cam1_dir = self.root_dir / "mav0" / "cam1" / "data"
        
        # Инерциалка
        self.imu0_dir = self.root_dir / "mav0" / "imu0"
        
        # Коордианты
        self.gt_dir = self.root_dir / "mav0" / "state_groundtruth_estimate0"
        
        # Пути к CSV-файлам.
        self.cam0_csv_path = self.cam0_dir / "data.csv"
        self.cam1_csv_path = self.cam1_dir / "data.csv"
        self.imu_csv_path = self.imu0_dir / "data.csv"
        self.gt_csv_path = self.gt_dir / "data.csv"

    def create_structure(self):
        self.cam0_dir.mkdir(parents=True, exist_ok=True)
        self.cam1_dir.mkdir(parents=True, exist_ok=True)
        self.imu0_dir.mkdir(parents=True, exist_ok=True)
        self.gt_dir.mkdir(parents=True, exist_ok=True)

    def init_csv_files(self):
        '''
        Создает CSV-файлы с заголовками.
        '''
        
        with open(self.imu_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "#timestamp [ns]",
                "w_RS_S_x [rad s^-1]",
                "w_RS_S_y [rad s^-1]",
                "w_RS_S_z [rad s^-1]",
                "a_RS_S_x [m s^-2]",
                "a_RS_S_y [m s^-2]",
                "a_RS_S_z [m s^-2]",
            ])

        with open(self.gt_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "#timestamp [ns]",
                "p_RS_R_x [m]",
                "p_RS_R_y [m]",
                "p_RS_R_z [m]",
                "q_RS_w []",
                "q_RS_x []",
                "q_RS_y []",
                "q_RS_z []",
                "v_RS_R_x [m s^-1]",
                "v_RS_R_y [m s^-1]",
                "v_RS_R_z [m s^-1]",
            ])

        with open(self.cam0_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["#timestamp [ns]", "filename"])

        with open(self.cam1_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["#timestamp [ns]", "filename"])

    def write_camera_image(self, camera_name: str, timestamp_ns: int, image_rgb: np.ndarray):
        """
        Сохраняет изображение камеры и добавляет строку в camera/data.csv.
        """
        if camera_name == "cam0":
            image_dir = self.cam0_dir
            csv_path = self.cam0_csv_path
        elif camera_name == "cam1":
            image_dir = self.cam1_dir
            csv_path = self.cam1_csv_path
        else:
            raise ValueError(f"Неизвестная камера: {camera_name}. Используй 'cam0' или 'cam1'.")

        filename = f"{timestamp_ns}.png"
        image_path = image_dir / filename

        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR) # конвертация из rgbв brg

        # Сохраняем png на диск.
        cv2.imwrite(str(image_path), image_bgr)

        # В csv пишем timestamp и имя файла относительно папки data.
        with open(csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp_ns, filename])
    
    def write_imu_row(self, timestamp_ns, wx, wy, wz, ax, ay, az):
        path = self.imu0_dir / "data.csv"

        with open(path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp_ns, wx, wy, wz, ax, ay, az])

    def write_gt_row(self, timestamp_ns, px, py, pz, qw, qx, qy, qz, vx, vy, vz):
        path = self.gt_dir / "data.csv"

        with open(path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp_ns, px, py, pz, qw, qx, qy, qz, vx, vy, vz])
    
    def write_command_log(self, commands, filename: str = "trajectory_commands.txt"):
        '''
        Сохраняет команды движения рядом с датасетом.
        '''
        path = self.root_dir / filename

        with open(path, "w", encoding="utf-8") as f:
            for i, command in enumerate(commands):
                f.write(f"{i}: {command}\n")

    