import torch
from torchvision import transforms
import cv2
from PIL import Image
import os
import argparse
from glob import glob
from model.model_irse import IR_101
from face_alignment import align
import tqdm

class Inference():
    def __init__(self, check_point, size=(112, 112), device = "cpu") -> None:
        self.means = (0.485, 0.456, 0.406)
        self.stds = (0.229, 0.224, 0.225)
        self.device = device
        self.transform = transforms.Compose([
                #    transforms.ToPILImage(),
                #    transforms.Grayscale(3),
                   transforms.ToTensor(),
                   transforms.Normalize(self.means, self.stds)
               ])
        self.size = size
        print("self.size", self.size)    
        self.model = self.load_model(check_point)
        
    def load_model(self, path):
        MODEL = IR_101(self.size)
        if self.device == "cpu":
            MODEL.load_state_dict(torch.load(path, map_location=torch.device('cpu')))
        else:
            MODEL.load_state_dict(torch.load(path))

        print("=> Loaded checkpoint '{}'".format(path))
        return MODEL.to(self.device).eval()

    def transform_image(self, path_images, batch=2):
        list_image = []
        batch_image = []
        print("path_images", len(path_images))
        for idx, path_image in tqdm.tqdm(enumerate(path_images)):
            frame = cv2.imread(path_image)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # aligned_rgb_img = align.get_aligned_face_cv2(frame, "cpu").resize((112,112))
        
            try:
                aligned_rgb_img = align.get_aligned_face_cv2(frame, "cpu").resize((112,112))
            except:
                print("can't read image", path_image)
                continue
            # print("aligned_rgb_img", aligned_rgb_img.size)
            # img = cv2.imread(path_image)
            # img = cv2.resize(img, self.size)
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = self.transform(aligned_rgb_img)
            list_image.append(img)
            if idx % (batch - 1) == 0 or idx == len(path_images) - 1:
                batch_image.append(torch.stack(list_image, dim=0))
                list_image = []
                
        return batch_image
    def l2_norm(self, input, axis=1):
        """l2 normalize
        """
        norm = torch.norm(input, 2, axis, True)
        output = torch.div(input, norm)
        return output

    def infer(self,list_path_images):
        batch_image = self.transform_image(list_path_images)
        # with open("test_embedding.txt","a") as f:
        #     for da in image:
        #         f.write("inseart-----\n"+str(da))
        # print("image", image.shape)
        list_embedding = []
        # print("len(batch_image)", len(batch_image))
        a = 0
        for image in batch_image:
            a += image.shape[0]
            images = image.to(self.device)
            # print("images", a)
            embedding = self.model(images)
            embedding = self.l2_norm(embedding)
            list_embedding.append(embedding.cpu().detach())
            
        return torch.cat(list_embedding, dim=0)

def main():
    parser = argparse.ArgumentParser(description='Infer model PyTorch Siamese Example')
    parser.add_argument('--path_image', type=str,
                        help='Directory of image')
    parser.add_argument('--path_checkpoint', type=str, default="/mnt/28857F714F734EE8/quan_tran/palmline/pytorch-siamese-triplet/results/Custom_1024_mg4/best_quarter.pth",
                        help='path to checkpoint')
    args = parser.parse_args()
                  
    prefix_image = ["jpg", "png", "bmp", "JPG", "PNG", "jpeg"]
    if os.path.isdir(args.path_image):
        list_path_file = glob(args.path_image+"/*")
        list_images = [i for i in list_path_file if i.split(".")[-1] in prefix_image]
    elif os.path.isfile(args.path_image):
        if args.path_image.split(".")[-1] in prefix_image:
            list_images = [args.path_image]
        else:
            raise TypeError(f"Only {prefix_image} is allowed")
    else:
        raise TypeError(f"path image had to directory of image or path to image, recheck it!")

    Infer = Inference(args.path_checkpoint)
    # print("list_images", list_images)
    embedding = Infer.infer(list_images)
    resut_distance = torch.cdist(embedding.cpu(), embedding.cpu(), 2)
    embedding = embedding.cpu().detach().tolist()
    print(resut_distance)


if __name__ == '__main__':
    main()
