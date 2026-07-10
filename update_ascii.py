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

def convert_to_ascii(image_path, mode="dark", width=64, height=50):
    # Chuỗi ký tự lặp lại tên của bạn
    text_sequence = "nadungvndawindev"
    seq_len = len(text_sequence)
    char_idx = 0
    
    img = Image.open(image_path)
    
    # Tăng độ tương phản và độ sáng để da mặt có màu sáng/trắng nổi bật như trong hình mẫu
    from PIL import ImageEnhance
    img = ImageEnhance.Contrast(img).enhance(2.0)   # Tăng tương phản gấp đôi
    img = ImageEnhance.Brightness(img).enhance(1.1) # Tăng độ sáng nhẹ
    
    # Sử dụng NEAREST để giữ độ sắc nét pixel art
    img = img.resize((width, height), Image.NEAREST)
    img_rgb = img.convert('RGB')
    
    # Lấy màu nền ở góc trên bên trái
    bg_color = img_rgb.getpixel((0, 0))
    
    ascii_rows = []
    for y in range(height):
        row_elements = []
        for x in range(width):
            r, g, b = img_rgb.getpixel((x, y))
            dist = ((r - bg_color[0])**2 + (g - bg_color[1])**2 + (b - bg_color[2])**2)**0.5
            
            if dist < 30:
                row_elements.append(" ")
            else:
                char = text_sequence[char_idx % seq_len]
                char_idx += 1
                
                if mode == "light":
                    # Giới hạn độ sáng trong Light Mode để hiển thị rõ trên nền trắng
                    r = r * 160 // 255
                    g = g * 160 // 255
                    b = b * 160 // 255
                else:
                    # Trong Dark Mode, tăng nhẹ độ sáng của các pixel không phải đen để các chữ sáng bóng hơn
                    r = min(255, int(r * 1.15))
                    g = min(255, int(g * 1.15))
                    b = min(255, int(b * 1.15))
                    
                color_hex = f"{r:02x}{g:02x}{b:02x}"
                row_elements.append((char, color_hex))
        ascii_rows.append(row_elements)
    return ascii_rows

def update_svg_ascii(svg_path, ascii_rows):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(svg_path, parser)
    root = tree.getroot()
    
    ascii_text_nodes = root.xpath(".//*[local-name()='text' and contains(@class, 'ascii')]")
    if not ascii_text_nodes:
        print(f"Không tìm thấy thẻ <text class='ascii'> trong {svg_path}")
        return
        
    ascii_node = ascii_text_nodes[0]
    
    # Cài đặt font size 10px, bold (font-weight 900) và khoảng cách chữ rất sát nhau (letter-spacing -1.5px)
    ascii_node.set("font-size", "10px")
    ascii_node.set("font-weight", "900")
    ascii_node.set("letter-spacing", "-1.5px")
    ascii_node.set("y", "20")
    
    # Xóa các thẻ tspan con cũ
    for child in list(ascii_node):
        ascii_node.remove(child)
        
    # Tạo 50 dòng mới từ y=20 đến y=510 (mỗi bước tăng 10px)
    for i, row in enumerate(ascii_rows):
        tspan = etree.Element("{http://www.w3.org/2000/svg}tspan")
        tspan.set("x", "15")
        tspan.set("y", str(20 + i * 10))
        tspan.tail = "\n"
        
        last_child = None
        current_text = ""
        current_color = None
        
        for item in row:
            if isinstance(item, str): # Khoảng trắng
                if current_color is not None:
                    child = etree.SubElement(tspan, "{http://www.w3.org/2000/svg}tspan")
                    child.set("fill", f"#{current_color}")
                    child.text = current_text
                    last_child = child
                    current_text = ""
                    current_color = None
                
                if last_child is not None:
                    last_child.tail = (last_child.tail or "") + item
                else:
                    tspan.text = (tspan.text or "") + item
            else:
                char, color = item
                if color == current_color:
                    current_text += char
                else:
                    if current_color is not None:
                        child = etree.SubElement(tspan, "{http://www.w3.org/2000/svg}tspan")
                        child.set("fill", f"#{current_color}")
                        child.text = current_text
                        last_child = child
                    else:
                        if current_text:
                            if last_child is not None:
                                last_child.tail = (last_child.tail or "") + current_text
                            else:
                                tspan.text = (tspan.text or "") + current_text
                    current_text = char
                    current_color = color
                    
        # Ghi nhận cụm cuối cùng ở cuối dòng
        if current_color is not None:
            child = etree.SubElement(tspan, "{http://www.w3.org/2000/svg}tspan")
            child.set("fill", f"#{current_color}")
            child.text = current_text
        elif current_text:
            if last_child is not None:
                last_child.tail = (last_child.tail or "") + current_text
            else:
                tspan.text = (tspan.text or "") + current_text
                
        ascii_node.append(tspan)
        
    # Ghi lại file SVG
    tree.write(svg_path, encoding='utf-8', xml_declaration=True)
    print(f"Đã cập nhật ASCII art chất lượng cao cho {os.path.basename(svg_path)}")

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
    
    # Sinh ASCII art màu cho Dark Mode
    ascii_dark = convert_to_ascii(image_path, mode="dark")
    update_svg_ascii("dark_mode.svg", ascii_dark)
    
    # Sinh ASCII art màu cho Light Mode
    ascii_light = convert_to_ascii(image_path, mode="light")
    update_svg_ascii("light_mode.svg", ascii_light)
    
    print("Hoàn tất cập nhật hình ảnh ASCII sắc nét!")

if __name__ == "__main__":
    main()
