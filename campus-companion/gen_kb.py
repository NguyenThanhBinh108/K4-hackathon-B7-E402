#!/usr/bin/env python3
"""
gen_kb.py — sinh Campus knowledge base chi tiet

VI SAO CO FILE NAY
------------------
Ban KB dau (13 muc) tra loi qua chung chung: hoi "trua nay an o dau" thi dap
"an tai khu campus dining duoc phep" — dung nhung vo dung, hoc vien van khong
biet di dau. KB phai co DIA DIEM CU THE (toa, tang), GIO, GIA, va CAC BUOC lam.

DU LIEU NAY LA MO PHONG — DOC KY
---------------------------------
Moi muc deu co truong "data_type": "mo_phong". Day KHONG phai thong tin that
cua VinUni. Nhom KHONG crawl website truong vi hai ly do:

  1. Luat hackathon (01-de-bai.md rang buoc 3): chi duoc dung data trong
     `data/` hoac data gia tu sinh.
  2. Quan trong hon — no pha chinh luan diem san pham. Bot nay ton tai de
     KHONG noi dieu chua kiem chung. Crawl duoc mot dia chi roi trich dan nhu
     "nguon chinh thuc", trong khi trang web co the da cu hoac parser doc nham,
     dung la kieu loi ma san pham hua se chan.

Khi trien khai that: thay noi dung tung muc bang thong tin do phong hanh chinh
cung cap, cap nhat `last_updated`, va doi `data_type` thanh "chinh_thuc".
Cau truc va code KHONG phai doi gi.

Chay:
    python3 gen_kb.py            # ghi de knowledge_base.json
    python3 gen_kb.py --check    # chi kiem tra, khong ghi
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "knowledge_base.json")

# (topic, scope, source_title, source_location, content)
# content viet SAT: co toa/tang, gio, gia, buoc lam. Tranh cau chung chung.
ENTRIES = [
    # ---------------- AN UONG ----------------
    ("lunch", "campus_general", "Campus Guide - An uong", "Campus Guide, muc An uong, tr.4",
     "Căng tin chính nằm ở tầng 1 Toà D, mở 07:00-19:00 các ngày trong tuần. Suất cơm 35.000-55.000đ, thanh toán bằng thẻ học viên hoặc tiền mặt. Giờ cao điểm 11:30-12:30 thường phải xếp hàng khoảng 10 phút."),
    ("lunch", "campus_general", "Campus Guide - An uong", "Campus Guide, muc An uong, tr.4",
     "Ngoài căng tin Toà D còn hai điểm ăn: quầy cà phê tầng trệt Toà A (07:30-17:00, bánh mì và đồ uống, 20.000-45.000đ) và khu food court tầng 2 Toà C (10:30-14:00 và 17:00-20:00, nhiều quầy món Việt và món Á)."),
    ("lunch", "course_specific", "Handbook AI Thuc Chien - Lich hoc", "Handbook, muc Lich hoc ca ngay",
     "Lớp học cả ngày có nghỉ trưa 12:00-13:15. Trong khung này căng tin Toà D đông nhất; nếu muốn nhanh thì food court Toà C tầng 2 vắng hơn khoảng 15 phút đầu giờ nghỉ."),
    ("bring_food", "campus_general", "Campus Guide - An uong va giu ve sinh", "Campus Guide, muc An uong, tr.5",
     "Mang đồ ăn từ nhà thì dùng khu bàn ăn chung tầng 1 Toà D hoặc khu ngoài trời sân giữa Toà B-C. Có 2 lò vi sóng ở góc phải khu bàn ăn Toà D và cây nước nóng-lạnh cạnh đó. Không ăn trong thư viện, phòng lab và phòng học."),
    ("bring_food", "campus_general", "Campus Guide - Giu ve sinh", "Campus Guide, muc Ve sinh chung",
     "Sau khi ăn, bỏ rác vào thùng phân loại ngay lối ra khu bàn ăn tầng 1 Toà D: nắp xanh cho rác hữu cơ, nắp vàng cho vỏ hộp và chai nhựa. Khay và bát đĩa của căng tin trả về quầy thu hồi cạnh cửa."),
    ("daily_food_support", "course_specific", "Thong bao ngay cua khoa", "Discord #announcements",
     "Suất ăn hỗ trợ của khoá (nếu có trong ngày) được thông báo trong #announcements trước 10:00 sáng hôm đó, kèm mã nhận suất. Không có thông báo nghĩa là hôm đó không có hỗ trợ. Trợ lý không tự xác nhận thông tin thay đổi theo ngày."),

    # ---------------- NGHI NGOI ----------------
    ("rest_area", "campus_general", "Campus Guide - Khu sinh hoat chung", "Campus Guide, muc Khong gian chung, tr.7",
     "Khu nghỉ có ghế dài ở tầng 2 Toà B (mở 07:00-21:00) và khu sofa sảnh tầng 1 Toà A. Đây là khu vực được phép nghỉ trưa. Không dùng phòng đọc thư viện làm chỗ ngủ."),
    ("rest_area", "campus_general", "Campus Guide - Khong gian ngoai troi", "Campus Guide, muc Khong gian chung",
     "Sân giữa Toà B và Toà C có ghế đá và mái che, dùng được cả khi trời mưa nhẹ. Khu vực này không giới hạn giờ nhưng đèn tắt sau 22:00."),

    # ---------------- THU VIEN ----------------
    ("library_hours", "campus_general", "Thong tin thu vien", "Trang thu vien, muc Gio mo cua",
     "Thư viện ở tầng 3-4 Toà A. Giờ mở cửa thường lệ: thứ Hai đến thứ Sáu 08:00-21:00, thứ Bảy 08:00-17:00, Chủ nhật đóng cửa. Giờ có thể đổi vào kỳ thi hoặc ngày lễ — thay đổi theo ngày phải hỏi Lab Coach hoặc xem thông báo tại quầy."),
    ("library_rules", "campus_general", "Noi quy thu vien", "Noi quy thu vien, muc Su dung khong gian",
     "Tầng 3 là khu yên tĩnh tuyệt đối, không nói chuyện và không nghe điện thoại. Tầng 4 là khu thảo luận nhóm, được trao đổi ở mức vừa phải. Không ăn uống ở cả hai tầng, trừ nước lọc đựng trong bình có nắp."),
    ("library_rules", "campus_general", "Noi quy thu vien", "Noi quy thu vien, muc Muon tra",
     "Học viên mượn tối đa 3 cuốn cùng lúc, thời hạn 14 ngày, gia hạn được 1 lần nếu không có người đặt trước. Quá hạn tính phí 5.000đ mỗi cuốn mỗi ngày. Mượn và trả tại quầy tầng 3 Toà A."),
    ("study_room", "campus_general", "Thong tin thu vien", "Trang thu vien, muc Phong hoc nhom",
     "Có 6 phòng học nhóm ở tầng 4 Toà A, sức chứa 4-8 người, đặt trước qua quầy thư viện hoặc form nội bộ. Mỗi nhóm đặt tối đa 2 tiếng một lượt. Đến muộn quá 15 phút thì phòng được nhả cho nhóm khác."),

    # ---------------- KY THUAT ----------------
    ("wifi", "campus_general", "Campus Guide - Wifi", "Campus Guide, muc Ha tang so, tr.9",
     "Wifi học viên dùng SSID 'VinUni-Student'. Đăng nhập bằng tài khoản email của trường, mật khẩu giống mật khẩu email. Khách dùng SSID 'VinUni-Guest', lấy mã tại quầy lễ tân tầng 1 Toà A, mã có hiệu lực 24 giờ."),
    ("wifi", "campus_general", "Campus Guide - Ho tro ky thuat", "Campus Guide, muc Ho tro",
     "Không đăng nhập được wifi: thử quên mạng rồi kết nối lại, kiểm tra đồng hồ máy đúng giờ. Vẫn lỗi thì liên hệ IT Helpdesk ở phòng 105 Toà A (08:00-17:30) hoặc nhắn kênh #lab-support."),
    ("printing", "campus_general", "Campus Guide - In an", "Campus Guide, muc Dich vu, tr.11",
     "Máy in cho học viên đặt ở tầng 2 Toà A (cạnh phòng 204) và tầng 3 Toà D. In đen trắng 500đ/trang, màu 2.000đ/trang, trừ vào tài khoản thẻ học viên. Gửi lệnh in qua cổng in nội bộ rồi quẹt thẻ tại máy để nhận bản in."),
    ("charging", "campus_general", "Campus Guide - Khong gian hoc", "Campus Guide, muc Tien ich",
     "Ổ cắm điện có ở tất cả bàn trong thư viện tầng 3-4 Toà A, khu bàn ăn tầng 1 Toà D và sảnh chờ tầng 1 Toà B. Khu sofa Toà A chỉ có ổ ở hàng ghế sát tường."),

    # ---------------- DI LAI ----------------
    ("parking", "campus_general", "Campus Guide - Gui xe", "Campus Guide, muc Di lai, tr.12",
     "Xe máy và xe đạp gửi ở hầm B1 Toà C, lối vào từ cổng phụ phía Đông. Mở 06:00-22:00. Xuất trình thẻ học viên khi vào và khi lấy xe. Mức phí do phòng hành chính công bố theo từng kỳ — trợ lý không tự nêu con số."),
    ("parking", "campus_general", "Campus Guide - Gui xe", "Campus Guide, muc Di lai",
     "Ô tô đỗ ở bãi ngoài trời phía Bắc, số chỗ hạn chế và ưu tiên cán bộ. Học viên muốn đăng ký chỗ ô tô phải làm đơn qua phòng hành chính, không đăng ký tại chỗ."),
    ("shuttle", "campus_general", "Campus Guide - Xe dua don", "Campus Guide, muc Di lai, tr.13",
     "Xe buýt đưa đón nội bộ dừng ở điểm trước sảnh Toà A. Khung giờ chạy và lộ trình được dán tại điểm dừng và cập nhật theo học kỳ. Lịch cụ thể theo ngày phải xem bảng tin tại điểm dừng."),

    # ---------------- RA VAO ----------------
    ("campus_access", "campus_general", "Campus Guide - Ra vao campus", "Campus Guide, muc An ninh, tr.3",
     "Ra vào campus bằng thẻ học viên quẹt tại cổng chính hoặc cổng phụ phía Đông. Cổng chính mở 06:00-22:00, ngoài giờ đó đi cổng phụ và ký sổ với bảo vệ."),
    ("campus_access", "campus_general", "Campus Guide - The hoc vien", "Campus Guide, muc An ninh",
     "Mất thẻ học viên: báo ngay phòng hành chính tầng 1 Toà A để khoá thẻ cũ, sau đó làm đơn cấp lại. Trong lúc chờ thẻ mới, đăng ký tạm với bảo vệ cổng để vẫn ra vào được."),
    ("campus_access", "campus_general", "Campus Guide - Khach den truong", "Campus Guide, muc An ninh",
     "Dẫn người ngoài vào campus phải đăng ký trước tại quầy lễ tân tầng 1 Toà A, khách xuất trình giấy tờ tuỳ thân và nhận thẻ khách. Thẻ khách trả lại khi ra về."),

    # ---------------- LOP HOC ----------------
    ("classroom_checkin", "course_specific", "Handbook AI Thuc Chien - Phong hoc", "Handbook, muc Phong hoc va check-in",
     "Phòng học của khoá ở tầng 2 và tầng 3 Toà B. Số phòng từng buổi được đăng trong #announcements trước buổi học ít nhất 1 ngày. Check-in bằng cách quẹt thẻ tại đầu đọc cạnh cửa phòng."),
    ("classroom_checkin", "course_specific", "Handbook AI Thuc Chien - Phong hoc", "Handbook, muc Phong hoc va check-in",
     "Đổi phòng đột xuất luôn được báo trong #announcements. Không thấy thông báo mà phòng khoá thì nhắn #lab-support, đừng tự tìm phòng khác vì có thể trùng lớp đang học."),
    ("attendance", "course_specific", "Handbook AI Thuc Chien - Diem danh", "Handbook, muc Diem danh, tr.6",
     "Điểm danh tính theo lượt quẹt thẻ đầu buổi. Đến muộn quá 15 phút tính là muộn, quá 30 phút tính là vắng buổi đó. Muộn hoặc vắng có lý do thì báo Lab Coach qua #lab-support trước giờ học."),
    ("attendance", "course_specific", "Handbook AI Thuc Chien - Diem danh", "Handbook, muc Diem danh",
     "Rời lớp sớm phải báo Lab Coach tại chỗ để được ghi nhận, nếu không hệ thống tính là vắng nửa buổi. Số buổi vắng tối đa và hệ quả do quy chế khoá quy định, hỏi Lab Coach để biết trường hợp của mình."),
    ("lab_equipment", "course_specific", "Handbook AI Thuc Chien - Phong lab", "Handbook, muc Trang thiet bi",
     "Phòng lab tầng 3 Toà B có máy trạm dùng chung, đăng ký lượt qua Lab Coach. Không tự cài phần mềm lên máy chung; cần công cụ gì thì nêu trong #lab-support để được cài đúng cách."),

    # ---------------- KENH & TAI LIEU ----------------
    ("discord_channels", "course_specific", "Handbook AI Thuc Chien - Kenh ho tro", "Handbook, muc Kenh lien lac, tr.2",
     "#announcements là nơi duy nhất đăng thông báo chính thức. #lab-support để nhờ Lab Coach hỗ trợ kỹ thuật và học tập. #resources chứa tài liệu, slide và link nộp bài. #general để trao đổi chung."),
    ("discord_channels", "course_specific", "Handbook AI Thuc Chien - Kenh ho tro", "Handbook, muc Kenh lien lac",
     "Câu hỏi riêng tư hoặc liên quan điểm số thì nhắn riêng Lab Coach, không đăng ở kênh chung. Thời gian phản hồi thường trong giờ hành chính các ngày có lịch học."),
    ("materials", "course_specific", "Handbook AI Thuc Chien - Tai lieu", "Handbook, muc Tai lieu, tr.5",
     "Slide, transcript và template bài nộp đều nằm ở #resources, đặt tên theo buổi. Link nộp bài luôn được đăng kèm trong thông báo của mốc tương ứng ở #announcements — dùng link mới nhất, link cũ có thể đã đóng."),
    ("materials", "course_specific", "Handbook AI Thuc Chien - Tai lieu", "Handbook, muc Tai lieu",
     "Recording buổi học được đăng lại trong #resources trong vòng 24 giờ sau buổi. Không thấy recording sau 24 giờ thì nhắn #lab-support, đừng hỏi lại ở kênh chung."),

    # ---------------- HO TRO KHAC ----------------
    ("health", "campus_general", "Campus Guide - Y te", "Campus Guide, muc Ho tro, tr.14",
     "Phòng y tế ở tầng 1 Toà A, phòng 108, trực 08:00-17:00 các ngày trong tuần. Có sơ cứu cơ bản và thuốc thông thường. Trường hợp khẩn cấp ngoài giờ thì gọi bảo vệ cổng chính để được hỗ trợ liên hệ y tế."),
    ("lost_and_found", "campus_general", "Campus Guide - Do that lac", "Campus Guide, muc Ho tro",
     "Đồ thất lạc được giữ tại quầy lễ tân tầng 1 Toà A trong 30 ngày. Mất đồ thì mô tả vật và thời điểm cho lễ tân; nhận lại phải xuất trình thẻ học viên."),
    ("quiet_room", "campus_general", "Campus Guide - Khong gian rieng", "Campus Guide, muc Khong gian chung",
     "Phòng yên tĩnh dùng để nghỉ ngơi hoặc cầu nguyện ở tầng 2 Toà A, phòng 210, mở trong giờ hành chính. Vào theo lượt, mỗi lượt tối đa 30 phút khi có người chờ."),
    ("convenience", "campus_general", "Campus Guide - Tien ich", "Campus Guide, muc Tien ich, tr.10",
     "Cửa hàng tiện lợi ở tầng 1 Toà C, mở 07:00-21:00. Máy ATM đặt cạnh cửa hàng. Máy bán nước tự động có ở tầng 1 và tầng 2 cả ba toà A, B, C."),
    ("emergency", "campus_general", "Campus Guide - Khan cap", "Campus Guide, muc An toan, tr.15",
     "Số trực bảo vệ dán tại mọi cửa thang máy và cạnh cửa ra vào từng toà. Điểm tập trung khi có báo cháy là sân giữa Toà B và Toà C. Lối thoát hiểm nằm ở hai đầu mỗi tầng, không để đồ chắn lối."),
    ("accessibility", "campus_general", "Campus Guide - Tiep can", "Campus Guide, muc An toan",
     "Cả bốn toà đều có thang máy và lối dốc cho xe lăn ở cửa chính. Nhà vệ sinh có buồng tiếp cận ở tầng 1 mỗi toà. Cần hỗ trợ di chuyển thì báo trước cho phòng hành chính tầng 1 Toà A."),
    ("dress_code", "campus_general", "Campus Guide - Quy dinh chung", "Campus Guide, muc Quy dinh, tr.2",
     "Trang phục gọn gàng, lịch sự khi lên lớp và vào thư viện. Phòng lab yêu cầu đi giày kín mũi. Sự kiện có quy định riêng sẽ ghi rõ trong thông báo của sự kiện đó."),
    ("event_booking", "campus_general", "Campus Guide - Su dung khong gian", "Campus Guide, muc Khong gian chung",
     "Mượn phòng hoặc không gian chung cho hoạt động nhóm ngoài giờ học phải đăng ký trước qua phòng hành chính tầng 1 Toà A, ít nhất 2 ngày làm việc, kèm danh sách người tham gia."),

    # ================= BO SUNG DOT 2 =================
    # ---------------- AN UONG (chi tiet hon) ----------------
    ("lunch", "campus_general", "Campus Guide - An uong", "Campus Guide, muc An uong, tr.4",
     "Căng tin Toà D có quầy chay ở vị trí trong cùng bên trái, phục vụ 11:00-13:30. Suất chay 30.000-40.000đ. Ngày lễ và cuối tuần quầy chay không mở."),
    ("lunch", "campus_general", "Campus Guide - An uong", "Campus Guide, muc An uong, tr.4",
     "Nạp tiền vào thẻ học viên để thanh toán tại căng tin: máy nạp đặt cạnh quầy thu ngân tầng 1 Toà D và tại phòng hành chính tầng 1 Toà A. Nạp tối thiểu 50.000đ, không hoàn lại tiền trong thẻ khi chưa dùng hết."),
    ("water", "campus_general", "Campus Guide - Tien ich", "Campus Guide, muc Tien ich, tr.10",
     "Cây nước lọc nóng-lạnh đặt ở hành lang gần thang máy mỗi tầng của cả bốn toà. Mang bình cá nhân để dùng; không có cốc giấy dùng một lần."),

    # ---------------- HOC TAP ----------------
    ("library_service", "campus_general", "Thong tin thu vien", "Trang thu vien, muc Dich vu",
     "Thư viện cho mượn laptop dùng tại chỗ, đăng ký tại quầy tầng 3 Toà A, trả trong ngày. Số lượng có hạn, ưu tiên theo thứ tự đăng ký, cần để lại thẻ học viên."),
    ("library_service", "campus_general", "Thong tin thu vien", "Trang thu vien, muc Ho tro",
     "Cần tìm tài liệu học thuật hoặc hướng dẫn tra cứu cơ sở dữ liệu, đặt lịch với thủ thư tại quầy tầng 3 Toà A hoặc để lại yêu cầu; thường được hỗ trợ trong 1-2 ngày làm việc."),
    ("locker", "campus_general", "Campus Guide - Tien ich", "Campus Guide, muc Tien ich, tr.11",
     "Tủ khoá cá nhân đặt ở hành lang tầng 1 Toà B, dùng theo ngày, tự mang khoá. Không để đồ qua đêm — đồ để lại sau 22:00 sẽ được chuyển về quầy đồ thất lạc tầng 1 Toà A."),
    ("scanner", "campus_general", "Campus Guide - In an", "Campus Guide, muc Dich vu, tr.11",
     "Máy scan đặt cạnh máy in tầng 2 Toà A. Scan miễn phí, file gửi về email trường của người dùng. Không scan được tài liệu khổ lớn hơn A3."),

    # ---------------- LOP HOC ----------------
    ("classroom_checkin", "course_specific", "Handbook AI Thuc Chien - Phong hoc", "Handbook, muc Phong hoc va check-in",
     "Quẹt thẻ không nhận ở đầu đọc cửa phòng: thử lại một lần, nếu vẫn không được thì báo Lab Coach ngay tại chỗ để được điểm danh thủ công. Đừng bỏ qua rồi báo sau buổi học."),
    ("makeup_class", "course_specific", "Handbook AI Thuc Chien - Hoc bu", "Handbook, muc Hoc bu",
     "Vắng buổi có lý do chính đáng thì xem recording trong #resources và làm bài của buổi đó theo hạn chung. Học bù trực tiếp chỉ tổ chức khi có thông báo riêng của khoá, không phải mặc định."),
    ("group_work", "course_specific", "Handbook AI Thuc Chien - Lam nhom", "Handbook, muc Lam viec nhom",
     "Nhóm 4-5 người, tự lập nhóm trong buổi đầu. Đổi nhóm sau khi đã chốt phải được Lab Coach đồng ý. Mỗi thành viên nộp riêng phần của mình, cả nhóm dùng chung một link repo."),
    ("deadline", "course_specific", "Handbook AI Thuc Chien - Nop bai", "Handbook, muc Nop bai va han",
     "Hạn nộp của từng mốc luôn được đăng trong #announcements kèm link nộp. Nộp muộn một mốc thì mốc đó không được tính điểm nộp. Trợ lý không tự xác nhận hạn cụ thể theo ngày — xem thông báo mới nhất."),
    ("grading", "course_specific", "Handbook AI Thuc Chien - Cham diem", "Handbook, muc Danh gia",
     "Điểm gồm phần nộp đúng hạn theo mốc và phần chấm trên bài nộp cuối. Chi tiết thang điểm nằm trong tài liệu rubric ở #resources. Thắc mắc về điểm cá nhân thì nhắn riêng Lab Coach, không hỏi ở kênh chung."),

    # ---------------- KY THUAT ----------------
    ("account", "course_specific", "Handbook AI Thuc Chien - Tai khoan", "Handbook, muc Tai khoan",
     "Tài khoản học trên nền tảng của khoá dùng email trường. Quên mật khẩu thì dùng chức năng khôi phục trên trang đăng nhập; không khôi phục được thì nhắn #lab-support kèm mã học viên, đừng gửi mật khẩu cho ai."),
    ("device", "course_specific", "Handbook AI Thuc Chien - Thiet bi", "Handbook, muc Chuan bi",
     "Học viên tự mang laptop. Yêu cầu tối thiểu và danh sách phần mềm cần cài được đăng trong #resources trước buổi đầu. Không có laptop thì đăng ký mượn máy trạm phòng lab tầng 3 Toà B qua Lab Coach."),
    ("software", "course_specific", "Handbook AI Thuc Chien - Cong cu", "Handbook, muc Cong cu",
     "Danh sách công cụ dùng trong khoá và hướng dẫn cài đặt nằm ở #resources. Gặp lỗi cài đặt thì đăng vào #lab-support kèm ảnh chụp lỗi và hệ điều hành đang dùng — mô tả suông thường phải hỏi lại nhiều lượt."),

    # ---------------- HANH CHINH ----------------
    ("certificate", "course_specific", "Handbook AI Thuc Chien - Chung nhan", "Handbook, muc Ket thuc khoa",
     "Chứng nhận hoàn thành cấp sau khi kết thúc khoá, điều kiện gồm số buổi tham dự tối thiểu và hoàn thành bài nộp cuối. Thời điểm và cách nhận được thông báo trong #announcements ở tuần cuối."),
    ("leave_request", "course_specific", "Handbook AI Thuc Chien - Nghi phep", "Handbook, muc Diem danh",
     "Xin nghỉ báo trước cho Lab Coach qua #lab-support, nêu buổi nghỉ và lý do. Báo trước giờ học được ghi nhận là nghỉ có phép; báo sau buổi học thì tính theo trường hợp vắng."),
    ("contact_admin", "campus_general", "Campus Guide - Lien he", "Campus Guide, muc Lien he, tr.16",
     "Phòng hành chính ở tầng 1 Toà A, phòng 101, làm việc 08:00-17:00 các ngày trong tuần, nghỉ trưa 12:00-13:00. Việc liên quan thẻ, đơn từ, đăng ký chỗ đỗ xe đều xử lý ở đây."),
    ("feedback", "course_specific", "Handbook AI Thuc Chien - Gop y", "Handbook, muc Phan hoi",
     "Góp ý về nội dung hoặc cách tổ chức khoá gửi qua form phản hồi đăng trong #announcements cuối mỗi giai đoạn, hoặc nhắn riêng Lab Coach. Góp ý ẩn danh được chấp nhận qua form."),

    # ---------------- AN TOAN & KHAC ----------------
    ("smoking", "campus_general", "Campus Guide - Quy dinh chung", "Campus Guide, muc Quy dinh, tr.2",
     "Toàn bộ khu vực trong nhà cấm hút thuốc, gồm cả thuốc lá điện tử. Khu vực được phép hút nằm ngoài trời phía sau Toà C, có biển chỉ dẫn."),
    ("noise", "campus_general", "Campus Guide - Quy dinh chung", "Campus Guide, muc Quy dinh",
     "Gọi điện và họp trực tuyến ở hành lang hoặc khu sofa tầng 1 Toà A, không gọi trong thư viện và phòng học. Sau 21:00 giữ yên tĩnh ở toàn bộ khu vực trong nhà."),
    ("weather", "campus_general", "Campus Guide - Tinh huong bat thuong", "Campus Guide, muc An toan, tr.15",
     "Thời tiết xấu hoặc sự cố khiến lịch học thay đổi thì thông báo được đăng trong #announcements và dán tại sảnh tầng 1 các toà. Không có thông báo nghĩa là lịch giữ nguyên."),
    ("visitor_parking", "campus_general", "Campus Guide - Gui xe", "Campus Guide, muc Di lai, tr.12",
     "Khách đến trường gửi xe tại bãi khách phía trước cổng chính, lấy vé tại chốt bảo vệ. Bãi hầm B1 Toà C chỉ dành cho học viên và cán bộ có thẻ."),
]


def build() -> list[dict]:
    kb, seen = [], {}
    for topic, scope, title, loc, content in ENTRIES:
        seen[topic] = seen.get(topic, 0) + 1
        kb.append({
            "id": f"campus_{topic}_{seen[topic]:03d}",
            "scope": scope,
            "topic": topic,
            "source_title": title,
            "source_location": loc,
            "last_updated": "2026-07-31",
            "data_type": "mo_phong",   # ĐỔI thành "chinh_thuc" khi thay bằng dữ liệu thật
            "content": content,
        })
    return kb


def check(kb: list[dict]) -> int:
    """Kiem tra chat luong — chan lai kieu 'chung chung' da lam hong ban dau."""
    bad = 0
    for e in kb:
        c = e["content"]
        if len(c) < 80:
            print(f"  [ngắn] {e['id']}: {len(c)} ký tự"); bad += 1
        # Muc ve dia diem thi phai neu duoc CHO NAO
        if e["topic"] in ("lunch", "bring_food", "rest_area", "library_hours", "study_room",
                          "printing", "parking", "health", "convenience", "quiet_room") \
           and not any(k in c for k in ("Toà", "tầng", "phòng", "hầm", "sân", "bãi")):
            print(f"  [thiếu địa điểm] {e['id']}"); bad += 1
        for f in ("id", "scope", "topic", "source_title", "source_location", "last_updated", "content"):
            if not e.get(f):
                print(f"  [thiếu trường {f}] {e['id']}"); bad += 1
    return bad


if __name__ == "__main__":
    if sys.platform == "win32":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError: pass

    kb = build()
    print(f"Sinh {len(kb)} mục · {len(set(e['topic'] for e in kb))} chủ đề")
    n_bad = check(kb)
    print(f"Kiểm tra: {'ĐẠT' if n_bad == 0 else f'{n_bad} vấn đề'}")

    if "--check" in sys.argv:
        sys.exit(0 if n_bad == 0 else 1)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    print(f"Đã ghi {OUT}")
