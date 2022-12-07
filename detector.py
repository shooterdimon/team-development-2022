import cv2
from cv2 import IMREAD_IGNORE_ORIENTATION
import numpy as np

def find_empty(detected_rows, width):
    empty_points = []
    detected_rows.insert(0, [detected_rows[0][0] - detected_rows[0][2], detected_rows[0][1], 0, detected_rows[0][3]])
    detected_rows.append([width, detected_rows[len(detected_rows)-1][1], width + detected_rows[len(detected_rows)-1][2] - detected_rows[len(detected_rows)-1][0], detected_rows[len(detected_rows)-1][3]])

    for i in range(0, len(detected_rows)-1):
        start_x_pt1 = detected_rows[i][0]
        end_x_pt1 = detected_rows[i][2]
        start_y_pt1 = detected_rows[i][1]
        end_y_pt1 = detected_rows[i][3]
        width1 = end_x_pt1 - start_x_pt1
        height1 = end_y_pt1 - start_y_pt1
        start_x_pt2 = detected_rows[i+1][0]
        end_x_pt2 = detected_rows[i+1][2]
        start_y_pt2 = detected_rows[i+1][1]
        end_y_pt2 = detected_rows[i+1][3]
        width2 = end_x_pt2 - start_x_pt2
        height2 = end_y_pt2 - start_y_pt2
        
        if ((width1+ height1)/2 + (width2+ height2)/2)/2 < (start_x_pt2 - end_x_pt1):
            num_of_empty_points = int(((start_x_pt2 - end_x_pt1)*2)/((width1+ height1)/2 +(width2+ height2)/2))
            for j in range(num_of_empty_points):

                empty_x = end_x_pt1 + int((j+1) * (start_x_pt2 - end_x_pt1)/(num_of_empty_points+1))
                empty_y = int(((detected_rows[i][3] + detected_rows[i][1])/2 + (detected_rows[i+1][3] + detected_rows[i+1][1])/2)/2)
                empty_points.append([empty_x, empty_y])

    return empty_points

def get_plants(img_to_detect, row_start_x_pt, row_start_y_pt):
    img_height = img_to_detect.shape[0]
    img_width = img_to_detect.shape[1]
    img_blob = cv2.dnn.blobFromImage(img_to_detect, 0.003922, (608, 416), swapRB=True, crop=False)

    detect_plants_model = cv2.dnn.readNetFromDarknet("model/plants_new_yolov4.cfg", "model/plants_new_yolov4_last.weights")
    detect_plants_layers = detect_plants_model.getLayerNames()
    detect_plants_output_layer = [detect_plants_layers[yolo_layer - 1] for yolo_layer in detect_plants_model.getUnconnectedOutLayers()]
    detect_plants_model.setInput(img_blob)

    rows_detection_layers = detect_plants_model.forward(detect_plants_output_layer)

    class_ids_list = []
    boxes_list = []
    confidences_list = []

    for object_detection_layer in rows_detection_layers:
        for object_detection in object_detection_layer:
        
            all_scores = object_detection[5:]
            predicted_class_id = np.argmax(all_scores)
        
            prediction_confidence = all_scores[predicted_class_id]

            if prediction_confidence > 0.4:
                bounding_box = object_detection[0:4] * np.array([img_width, img_height, img_width, img_height])
                (box_center_x_pt, box_center_y_pt, box_width, box_height) = bounding_box.astype("int")
                start_x_pt = int(box_center_x_pt - (box_width / 2))
                start_y_pt = int(box_center_y_pt - (box_height / 2))
                class_ids_list.append(predicted_class_id)
                confidences_list.append(float(prediction_confidence))
                boxes_list.append([start_x_pt, start_y_pt, int(box_width), int(box_height)])


    max_value_ids = cv2.dnn.NMSBoxes(boxes_list, confidences_list, 0.4, 0.6)

    detected_rows = []
    precision = 0
    for id in max_value_ids:
    
        start_x_pt = max(0, boxes_list[id][0])
        start_y_pt = boxes_list[id][1]
        end_x_pt = start_x_pt +  boxes_list[id][2]
        end_y_pt = start_y_pt + boxes_list[id][3]
        current_row = [start_x_pt + row_start_x_pt, start_y_pt + row_start_y_pt, end_x_pt + row_start_x_pt, end_y_pt + row_start_y_pt]
        precision += confidences_list[id]
        detected_rows.append(current_row)

    return detected_rows, precision

def detect_plants(image_names):
    total_plants = 0
    total_empty = 0
    total_precision = 0
    total_rows = 0
    for image in image_names:

        img_to_detect = cv2.imread(f'images/{image[0]}.jpg')

        img_height = img_to_detect.shape[0]
        img_width = img_to_detect.shape[1]

        img_blob = cv2.dnn.blobFromImage(img_to_detect, 0.003922, (608, 608), swapRB=True, crop=False)

        row_color=["0,255,0"]
        row_color = [np.array(every_color.split(",")).astype("int") for every_color in row_color]
        row_color = np.array(row_color)
        row_color = np.tile(row_color, (1,1))

        detect_rows_model = cv2.dnn.readNetFromDarknet("model/row_yolov4.cfg", "model/row_yolov4_best.weights")

        detect_rows_layers = detect_rows_model.getLayerNames()

        detect_rows_output_layer = [detect_rows_layers[yolo_layer - 1] for yolo_layer in detect_rows_model.getUnconnectedOutLayers()]
        detect_rows_model.setInput(img_blob)

        rows_detection_layers = detect_rows_model.forward(detect_rows_output_layer)

        class_ids_list = []
        boxes_list = []
        confidences_list = []

        for object_detection_layer in rows_detection_layers:
            for object_detection in object_detection_layer:
                
                all_scores = object_detection[5:]
                predicted_class_id = np.argmax(all_scores)
                
                prediction_confidence = all_scores[predicted_class_id]

                if prediction_confidence > 0.4:

                    bounding_box = object_detection[0:4] * np.array([img_width, img_height, img_width, img_height])
                    (box_center_x_pt, box_center_y_pt, box_width, box_height) = bounding_box.astype("int")
                    start_x_pt = int(box_center_x_pt - (box_width / 2))
                    start_y_pt = int(box_center_y_pt - (box_height / 2))
                    class_ids_list.append(predicted_class_id)
                    confidences_list.append(float(prediction_confidence))
                    boxes_list.append([start_x_pt, start_y_pt, int(box_width), int(box_height)])


        max_value_ids = cv2.dnn.NMSBoxes(boxes_list, confidences_list, 0.4, 0.6)
        detected_plants = []
        detected_empty = []
        total_rows += len(max_value_ids)
        for id in max_value_ids:

            start_x_pt = 0
            start_y_pt = boxes_list[id][1]
            end_x_pt = img_width
            end_y_pt = start_y_pt + boxes_list[id][3]
            region = img_to_detect[start_y_pt:end_y_pt, start_x_pt:end_x_pt]
            plants_in_row, precision = get_plants(region, start_x_pt, start_y_pt)
            empty_in_row = find_empty(sorted(plants_in_row), region.shape[1])
            detected_plants.append(plants_in_row)
            detected_empty.append(empty_in_row)
            total_precision += precision
            

        for row in detected_plants:
            total_plants += len(row)
            for plant in row:
                cv2.circle(img_to_detect, (int((plant[0]+plant[2])/2), int((plant[1]+plant[3])/2)), 10, (0, 255, 0), -1)
        for row in detected_empty:
            total_empty +=len(row)
            for empty in row:
                cv2.circle(img_to_detect, (empty[0], empty[1]), 10, (0, 0, 255), -1)
            #for box in row:

                #box_color = row_color[0]
                #box_color = [int(c) for c in box_color]
                #cv2.rectangle(img_to_detect, (box[0], box[1]), (box[2], box[3]), box_color, 1)

        #cv2.imshow("Detection Output", img_to_detect)
        #cv2.waitKey()
        cv2.imwrite(f'images/_{image[0]}.jpg' ,img_to_detect)

    return total_rows, total_plants, total_empty
