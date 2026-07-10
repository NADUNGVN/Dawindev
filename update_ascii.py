import os
import sys
import io
import base64
from lxml import etree

try:
    from PIL import Image
except ImportError:
    print("Thư viện Pillow chưa được cài đặt. Đang tiến hành cài đặt...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

def get_transparent_avatar_base64(image_path):
    img = Image.open(image_path)
    img = img.convert("RGBA")
    
    # Lấy màu nền ở góc trên bên trái (0, 0)
    bg_color = img.getpixel((0, 0))
    
    # Duyệt qua các pixel để xóa nền tím
    datas = img.getdata()
    new_data = []
    for item in datas:
        r, g, b, a = item
        # Tính khoảng cách màu Euclidean
        dist = ((r - bg_color[0])**2 + (g - bg_color[1])**2 + (b - bg_color[2])**2)**0.5
        if dist < 30:
            new_data.append((0, 0, 0, 0)) # Trở thành trong suốt (Transparent)
        else:
            new_data.append(item)
    img.putdata(new_data)
    
    # Resize về kích thước 300x300 bằng NEAREST để giữ nguyên độ sắc nét pixel art
    img = img.resize((300, 300), Image.NEAREST)
    
    # Lưu vào buffer dạng PNG và mã hóa Base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return base64_data

def update_svg_with_image(svg_path, base64_data):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(svg_path, parser)
    root = tree.getroot()
    
    # Tìm thẻ text có class="ascii" để thay thế
    ascii_text_nodes = root.xpath(".//*[local-name()='text' and contains(@class, 'ascii')]")
    # Hoặc tìm thẻ image đã được thay thế trước đó
    image_nodes = root.xpath(".//*[local-name()='image']")
    
    if ascii_text_nodes:
        text_node = ascii_text_nodes[0]
        # Tạo thẻ <image> mới
        image_el = etree.Element("{http://www.w3.org/2000/svg}image")
        image_el.set("x", "35")
        image_el.set("y", "115")
        image_el.set("width", "300")
        image_el.set("height", "300")
        image_el.set("href", f"data:image/png;base64,{base64_data}")
        
        # Thay thế thẻ text bằng thẻ image
        parent = text_node.getparent()
        parent.replace(text_node, image_el)
    elif image_nodes:
        # Cập nhật href nếu thẻ <image> đã tồn tại
        image_nodes[0].set("href", f"data:image/png;base64,{base64_data}")
        image_nodes[0].set("x", "35")
        image_nodes[0].set("y", "115")
        image_nodes[0].set("width", "300")
        image_nodes[0].set("height", "300")
    else:
        print(f"Không tìm thấy thẻ thích hợp trong {svg_path}")
        return
        
    # Ghi đè file SVG
    tree.write(svg_path, encoding='utf-8', xml_declaration=True)
    print(f"Đã nhúng ảnh đại diện trực tiếp thành công cho {os.path.basename(svg_path)}")

def main():
    # Tìm file ảnh avatar.png hoặc avatar.jpg
    image_path = None
    for ext in ["png", "jpg", "jpeg"]:
        path = f"avatar.{ext}"
        if os.path.exists(path):
            image_path = path
            break
            
    if not image_path:
        print("LỖI: Không tìm thấy file avatar.png hoặc avatar.jpg trong thư mục hiện tại.")
        return
        
    print(f"Đang xử lý ảnh: {image_path}")
    
    # Lấy chuỗi base64 của ảnh trong suốt
    base64_data = get_transparent_avatar_base64(image_path)
    
    # Nhúng trực tiếp vào dark_mode.svg và light_mode.svg
    update_svg_with_image("dark_mode.svg", base64_data)
    update_svg_with_image("light_mode.svg", base64_data)
    
    print("Hoàn tất cập nhật ảnh chân dung gốc!")

if __name__ == "__main__":
    main()
