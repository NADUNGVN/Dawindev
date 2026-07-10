import os
import sys
from lxml import etree

try:
    from PIL import Image
except ImportError:
    print("Thư viện Pillow chưa được cài đặt. Đang tiến hành cài đặt...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

def convert_to_ascii(image_path, mode="dark", width=44, height=25):
    # Dải ký tự xếp theo mật độ từ tối đến sáng
    chars_dark = " .'`,;:!il*{%H@M"
    chars_light = "M@H%*{li!:;,'. "
    chars = chars_dark if mode == "dark" else chars_light
    
    img = Image.open(image_path)
    img = img.resize((width, height))
    
    # Lấy màu nền ở góc trên bên trái (0, 0)
    img_rgb = img.convert('RGB')
    bg_color = img_rgb.getpixel((0, 0))
    
    img_gray = img.convert('L') # Chuyển sang ảnh xám (grayscale)
    
    ascii_rows = []
    for y in range(height):
        row = ""
        for x in range(width):
            r, g, b = img_rgb.getpixel((x, y))
            # Tính khoảng cách Euclidean giữa màu pixel và màu nền
            dist = ((r - bg_color[0])**2 + (g - bg_color[1])**2 + (b - bg_color[2])**2)**0.5
            
            if dist < 30:
                row += " " # Màu nền chuyển thành khoảng trắng để trong suốt
            else:
                pixel = img_gray.getpixel((x, y))
                char_idx = pixel * (len(chars) - 1) // 255
                row += chars[char_idx]
        ascii_rows.append(row)
    return ascii_rows

def update_svg_ascii(svg_path, ascii_rows):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(svg_path, parser)
    root = tree.getroot()
    
    # Tìm thẻ <text class="ascii">
    # Dùng local-name() vì SVG có XML namespace
    ascii_text_nodes = root.xpath(".//*[local-name()='text' and contains(@class, 'ascii')]")
    if not ascii_text_nodes:
        print(f"Không tìm thấy thẻ <text class='ascii'> trong {svg_path}")
        return
        
    ascii_node = ascii_text_nodes[0]
    
    # Xóa các thẻ tspan con hiện tại
    for child in list(ascii_node):
        ascii_node.remove(child)
        
    # Tạo các thẻ tspan mới cho mỗi dòng ASCII
    # Tọa độ y bắt đầu từ 30 và tăng 20px mỗi dòng
    for i, row in enumerate(ascii_rows):
        tspan = etree.Element("{http://www.w3.org/2000/svg}tspan")
        tspan.set("x", "15")
        tspan.set("y", str(30 + i * 20))
        # Thay thế ký tự đặc biệt để an toàn cho XML (ví dụ & thành &amp;, < thành &lt;)
        # lxml sẽ tự động escape khi ghi file
        tspan.text = row
        tspan.tail = "\n"
        ascii_node.append(tspan)
        
    # Ghi lại file SVG
    tree.write(svg_path, encoding='utf-8', xml_declaration=True)
    print(f"Đã cập nhật ASCII art thành công cho {os.path.basename(svg_path)}")

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
        print("Vui lòng lưu bức ảnh của bạn vào thư mục này với tên 'avatar.png' trước.")
        return
        
    print(f"Đang xử lý ảnh: {image_path}")
    
    # Sinh ASCII art cho Dark Mode
    ascii_dark = convert_to_ascii(image_path, mode="dark")
    update_svg_ascii("dark_mode.svg", ascii_dark)
    
    # Sinh ASCII art cho Light Mode
    ascii_light = convert_to_ascii(image_path, mode="light")
    update_svg_ascii("light_mode.svg", ascii_light)
    
    print("Hoàn tất cập nhật hình ảnh ASCII!")

if __name__ == "__main__":
    main()
