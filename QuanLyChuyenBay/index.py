from _pydatetime import timedelta
from datetime import datetime
import time
from QuanLyChuyenBay import app, dao, admin, login, utils
from flask import render_template, request, redirect, session, jsonify, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
import cloudinary.uploader
from QuanLyChuyenBay import app, dao, db, gio_mua_toi_da, gio_ban_toi_da, thoi_gian_bay_toi_thieu, \
    san_bay_trung_gian_toi_da, thoi_gian_dung_toi_da, thoi_gian_dung_toi_thieu
from QuanLyChuyenBay.dao import load_san_bay, get_chuyen_bay_by_id, get_available_seats, update_seat_status, \
    get_customer_by_phone, create_customer, sell_ticket, load_chuyen_bay, get_doanh_thu_theo_thang
from QuanLyChuyenBay.models import ChuyenBay, SanBayTrungGian, TuyenBay, KhachHang, GioiTinhEnum, SanBay, GheMayBay, Ve, \
    MayBay
from flask import render_template
from __init__ import QuyDinh
import hashlib



@app.route('/bao_cao_doanh_thu', methods=['GET', 'POST'])
def bao_cao_doanh_thu():
    thang = request.args.get('month')
    bao_cao = []
    tong_doanh_thu = 0
    month_stats = []

    if thang:
        bao_cao = get_doanh_thu_theo_thang(thang)
        tong_doanh_thu = sum(row.doanh_thu_hang_1 + row.doanh_thu_hang_2 for row in bao_cao)

        # Thống kê doanh thu theo từng tháng
        for i in range(1, 13):
            monthly_data = get_doanh_thu_theo_thang(i)
            monthly_revenue = sum(row.doanh_thu_hang_1 + row.doanh_thu_hang_2 for row in monthly_data)
            month_stats.append((i, monthly_revenue))

    chuyen_bays = ChuyenBay.query.all()

    return render_template('bao_cao_doanh_thu.html', stats=bao_cao, cb=chuyen_bays, month=thang, tong_doanh_thu=tong_doanh_thu, month_stats=month_stats)


@app.route('/')
def home():
    ten_dia_diem = load_san_bay()
    from_place = ''
    to_place = ''
    date = ''
    chuyen_bays = []

    if request.method == 'POST':
        from_place = request.form.get('from', '')
        to_place = request.form.get('to', '')
        date = request.form.get('date', '')
        chuyen_bays = dao.load_chuyen_bay(from_place, to_place, date)

    return render_template('index.html', ten_dia_diem=ten_dia_diem,
                           from_place=from_place, to_place=to_place, date=date, chuyen_bays=chuyen_bays)


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/register', methods=['GET', 'POST'])
def user_register():
    err_msg = ''
    if request.method.__eq__('POST'):  # So sánh với __eq__
        password = request.form['password']
        confirm = request.form['confirm']
        if password.__eq__(confirm):  # So sánh mật khẩu với __eq__
            anh_dai_dien = ''
            if request.files:
                res = cloudinary.uploader.upload(request.files['anh_dai_dien'])
                anh_dai_dien = res['secure_url']

            try:
                dao.register(name=request.form['name'],
                             username=request.form['username'],
                             password=password, anh_dai_dien=anh_dai_dien)
                return redirect('/login')
            except:
                err_msg = 'Hệ thống đang lỗi. Vui lòng thử lại sau !!'
        else:
            err_msg = 'Mật khẩu không khớp!'  # Thông báo mật khẩu không khớp

    return render_template('register.html', err_msg=err_msg)





@app.route('/login', methods=['GET', 'POST'])
def login_my_user():
    err_msg = ''
    if request.method.__eq__('POST'):
        username = request.form['username']
        password = request.form['password']
        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user=user)
            n = request.args.get('next')
            return redirect(n if n else '/')
        else:
            err_msg = 'Tên đăng nhập hoặc Mật khẩu không chính xác !!!'
    return render_template('login.html', err_msg=err_msg)


@app.route('/logout')
def logout_my_user():
    logout_user()
    return redirect('/login')


@app.route('/login-admin', methods=['POST'])
def admin_login():
    username = request.form['username']
    password = request.form['password']
    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)

    return redirect('/admin')


@app.route('/order', methods=['GET', 'POST'])
def tra_cuu_chuyen_bay():
    ten_dia_diem = load_san_bay()
    from_place = ''
    to_place = ''
    date = ''
    chuyen_bays = []

    if request.method == 'POST':
        from_place = request.form.get('from', '')
        to_place = request.form.get('to', '')
        date = request.form.get('date', '')
        chuyen_bays = dao.load_chuyen_bay(from_place, to_place, date)

    return render_template('order.html', ten_dia_diem=ten_dia_diem,
                           from_place=from_place, to_place=to_place, date=date, chuyen_bays=chuyen_bays)


@app.route('/ordernow', methods=['GET', 'POST'])
def tra_cuu_chuyen_bay_staff():
    ten_dia_diem = load_san_bay()
    from_place = ''
    to_place = ''
    date = ''
    chuyen_bays = []

    if request.method == 'POST':
        from_place = request.form.get('from', '')
        to_place = request.form.get('to', '')
        date = request.form.get('date', '')
        chuyen_bays = dao.load_chuyen_bay(from_place, to_place, date)

    return render_template('ordernow.html', ten_dia_diem=ten_dia_diem,
                           from_place=from_place, to_place=to_place, date=date, chuyen_bays=chuyen_bays)



@app.route('/detail_flight/<int:flight_id>')
def detail_flight(flight_id):
    chuyen_bay = dao.get_chuyen_bay_by_id(flight_id)
    tuyen_bay = dao.get_tuyen_bay_by_id(chuyen_bay.tuyen_bay_id)
    san_bay_di = dao.get_san_bay_by_id(tuyen_bay.san_bay_di_id)
    san_bay_den = dao.get_san_bay_by_id(tuyen_bay.san_bay_den_id)

    from_place = request.args.get('from', '')
    to_place = request.args.get('to', '')
    date = request.args.get('date', '')

    return render_template('detail_flight.html', chuyen_bay=chuyen_bay, tuyen_bay=tuyen_bay, san_bay_di=san_bay_di,
                           san_bay_den=san_bay_den, from_place=from_place, to_place=to_place, date=date)


@app.route('/thanh-toan/<int:chuyen_bay_id>/<string:hang_ve>', methods=['GET', 'POST'])
def thanh_toan(chuyen_bay_id, hang_ve):
    # Truy xuất thông tin chuyến bay
    chuyen_bay = dao.get_chuyen_bay_by_id(chuyen_bay_id)

    # Cấu hình giá vé dựa trên hạng vé
    if hang_ve == 'hang_1':
        gia_ve = chuyen_bay.gia_ve_hang_1
    else:
        gia_ve = chuyen_bay.gia_ve_hang_2

    # Truyền thông tin vào template thanh toán
    return render_template('thanh_toan.html', chuyen_bay=chuyen_bay, hang_ve=hang_ve, gia_ve=gia_ve)


@app.route('/xacnhanthanhtoan/<int:chuyen_bay_id>/<hang_ve>', methods=['GET', 'POST'])
def xac_nhan_thanh_toan(chuyen_bay_id, hang_ve):
    # Lấy thông tin chuyến bay và hạng vé
    chuyen_bay = dao.get_chuyen_bay_by_id(chuyen_bay_id)

    if hang_ve == 'hang_1':
        gia_ve = chuyen_bay.gia_ve_hang_1
    elif hang_ve == 'hang_2':
        gia_ve = chuyen_bay.gia_ve_hang_2
    else:
        # Nếu không phải hạng 1 hoặc hạng 2, trả về trang lỗi hoặc thông báo
        return "Hạng vé không hợp lệ", 400

    # Truyền thông tin chuyến bay và hạng vé vào trang xác nhận thanh toán
    return render_template('xac_nhan_thanh_toan.html', chuyen_bay=chuyen_bay, gia_ve=gia_ve, hang_ve=hang_ve)


@app.route('/seats/<int:chuyenbay_id>/<ticket_class>')
def available_seats(chuyenbay_id, ticket_class):
    chuyenbay = ChuyenBay.query.get_or_404(chuyenbay_id)
    may_bay = chuyenbay.may_bay

    # Lấy danh sách ghế có sẵn từ hàm get_available_seats
    hangghes = get_available_seats(may_bay.id, ticket_class)

    # Xác định giá vé dựa trên hạng ghế
    gia_ve = chuyenbay.gia_ve_hang_1 if ticket_class == 'hang_1' else chuyenbay.gia_ve_hang_2

    return render_template('seats.html', chuyenbay=chuyenbay, hangghes=hangghes, gia_ve=gia_ve)


# app.py

@app.route('/select_seat/<int:ghes_id>')
def select_seat(ghes_id):
    # Lưu thông tin ghế được chọn nhưng không thay đổi trạng thái
    ghe = GheMayBay.query.get_or_404(ghes_id)

    # Chuyển hướng người dùng tới trang thanh toán
    return redirect(url_for('process_payment', ghes_id=ghes_id))


@app.route('/customer/<int:flight_id>/<string:ticket_class>', methods=['GET', 'POST'])
@login_required
def customer(flight_id, ticket_class):
    from_place = request.args.get('from')
    to_place = request.args.get('to')
    date = request.args.get('date')
    error_msg = None
    return render_template('customer.html', flight_id=flight_id, ticket_class=ticket_class, from_place=from_place,
                           to_place=to_place, date=date, error_msg=error_msg)




@app.route('/momo_payment/<int:chuyen_bay_id>/<string:hang_ve>', methods=['POST'])
@login_required
def momo_payment(flight_id, ticket_class):
    try:
        khach_hang_id = request.form.get('khach_hang_id')
        user_id = current_user.id

        chuyen_bay = dao.get_chuyen_bay_by_id(flight_id)
        price = chuyen_bay.gia_ve_hang_1 if ticket_class == 'hang_1' else chuyen_bay.gia_ve_hang_2

        # # Gọi API của MoMo để thực hiện thanh toán
        # pay_url = dao.momo_payment(flight_id, ticket_class)
        #
        # # Chuyển hướng người dùng đến URL thanh toán của MoMo
        # return redirect(pay_url)
        return redirect('/')
    except Exception as e:
        return str(e)


@app.route('/momo_return')
def momo_return():
    try:
        # Kiểm tra kết quả thanh toán từ MoMo
        result = request.args
        if result.get('errorCode') == '0':
            # Lưu thông tin vé vào cơ sở dữ liệu
            flight_id = result.get('flight_id')
            ticket_class = result.get('ticket_class')
            khach_hang_id = result.get('khach_hang_id')
            user_id = current_user.id
            chuyen_bay = dao.get_chuyen_bay_by_id(flight_id)
            price = chuyen_bay.gia_ve_hang_1 if ticket_class == 'hang_1' else chuyen_bay.gia_ve_hang_2
            dao.save_ticket(khach_hang_id, user_id, flight_id, ticket_class, price)
            return "Thanh toán bằng MoMo thành công!"
        else:
            return "Thanh toán bằng MoMo thất bại!"
    except Exception as e:
        return str(e)


@app.route('/vnpay_payment/<int:chuyen_bay_id>/<string:hang_ve>', methods=['POST'])
@login_required
def vnpay_payment(flight_id, ticket_class):
    try:
        khach_hang_id = request.form.get('khach_hang_id')
        user_id = current_user.id

        chuyen_bay = dao.get_chuyen_bay_by_id(flight_id)
        price = chuyen_bay.gia_ve_hang_1 if ticket_class == 'hang_1' else chuyen_bay.gia_ve_hang_2

        # Gọi API của VNPay để thực hiện thanh toán
        pay_url = dao.vnpay_payment(flight_id, ticket_class)

        # Chuyển hướng người dùng đến URL thanh toán của VNPay
        return redirect(pay_url)
    except Exception as e:
        return str(e)


@app.route('/vnpay_return')
def vnpay_return():
    try:
        # Kiểm tra kết quả thanh toán từ VNPay
        result = request.args
        if result.get('vnp_ResponseCode') == '00':
            # Lưu thông tin vé vào cơ sở dữ liệu
            flight_id = result.get('flight_id')
            ticket_class = result.get('ticket_class')
            khach_hang_id = result.get('khach_hang_id')
            user_id = current_user.id
            chuyen_bay = dao.get_chuyen_bay_by_id(flight_id)
            price = chuyen_bay.gia_ve_hang_1 if ticket_class == 'hang_1' else chuyen_bay.gia_ve_hang_2
            dao.save_ticket(khach_hang_id, user_id, flight_id, ticket_class, price)
            return "Thanh toán bằng VNPay thành công!"
        else:
            return "Thanh toán bằng VNPay thất bại!"
    except Exception as e:
        return str(e)


@app.route('/xac_nhan_thanh_toan-success/<int:chuyen_bay_id>/<string:hang_ve>', methods=['POST'])
@login_required
def xac_nhan_thanh_toan_success(chuyen_bay_id, hang_ve):
    try:
        # Handle successful payment logic here
        return "Payment Successful!"
    except Exception as e:
        return str(e)


@app.route('/xac_nhan_thanh_toan-failure/<int:chuyen_bay_id>/<string:hang_ve>', methods=['POST'])
@login_required
def xac_nhan_thanh_toan_failure(chuyen_bay_id, hang_ve):
    try:
        # Handle failed payment logic here
        return "Payment Failed!"
    except Exception as e:
        return str(e)



@app.route('/tao_san_bay', methods=['GET', 'POST'])
def tao_san_bay():
    if request.method == 'POST':
        ten_sb = request.form['ten_sb']
        ten_khu_vuc = request.form['ten_khu_vuc']

        san_bay_moi = SanBay(ten_sb=ten_sb, ten_khu_vuc=ten_khu_vuc)
        db.session.add(san_bay_moi)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('new_airport.html')


@app.route('/tao_may_bay', methods=['GET', 'POST'])
def tao_may_bay():
    if request.method == 'POST':
        ten_may_bay = request.form['ten_may_bay']
        tinh_trang_hoat_dong = bool(int(request.form['tinh_trang_hoat_dong']))
        so_luong_hang_ghe_1 = int(request.form['so_luong_hang_ghe_1'])
        so_luong_hang_ghe_2 = int(request.form['so_luong_hang_ghe_2'])
        nam_san_xuat = int(request.form['nam_san_xuat'])

        may_bay_moi = MayBay(ten_may_bay=ten_may_bay,
                             tinh_trang_hoat_dong=tinh_trang_hoat_dong,
                             so_luong_hang_ghe_1=so_luong_hang_ghe_1,
                             so_luong_hang_ghe_2=so_luong_hang_ghe_2,
                             nam_san_xuat=nam_san_xuat)

        db.session.add(may_bay_moi)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('new_airplane.html')


@app.route('/tao_tuyen_bay', methods=['GET', 'POST'])
def tao_tuyen_bay():
    san_bays = SanBay.query.all()

    if request.method == 'POST':
        san_bay_di_id = request.form['san_bay_di_id']
        san_bay_den_id = request.form['san_bay_den_id']
        khoang_cach = float(request.form['khoang_cach'])
        thoi_gian_bay = int(request.form['thoi_gian_bay'])

        tuyen_bay_moi = TuyenBay(san_bay_di_id=san_bay_di_id,
                                 san_bay_den_id=san_bay_den_id,
                                 khoang_cach=khoang_cach,
                                 thoi_gian_bay=thoi_gian_bay)

        db.session.add(tuyen_bay_moi)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('new_route.html', san_bays=san_bays)


@app.route('/ban_ve', methods=['GET', 'POST'])
def ban_ve():
    chuyen_bays = ChuyenBay.query.all()  # Lấy tất cả các chuyến bay

    if request.method == 'POST':
        chuyen_bay_id = request.form['chuyen_bay_id']
        ten_hanh_khach = request.form['ten_hanh_khach']
        cmnd = request.form['cmnd']
        dien_thoai = request.form['dien_thoai']
        hang_ve = int(request.form['hang_ve'])

        chuyen_bay = ChuyenBay.query.get(chuyen_bay_id)
        now = datetime.now()

        # Kiểm tra xem chuyến bay có còn vé không và còn 4 giờ trước khi bay không
        if chuyen_bay.ngay_gio_bay - now < timedelta(hours=4):
            return "Không thể bán vé cho chuyến bay quá gần giờ khởi hành", 400

        if hang_ve == 1:
            # Kiểm tra số lượng ghế hạng 1 còn lại
            if chuyen_bay.gia_ve_hang_1 <= 0:
                return "Không còn vé hạng 1", 400
        else:
            # Kiểm tra số lượng ghế hạng 2 còn lại
            if chuyen_bay.gia_ve_hang_2 <= 0:
                return "Không còn vé hạng 2", 400

        # Tạo hành khách mới và vé mới
        hanh_khach = KhachHang(ten_hanh_khach=ten_hanh_khach, cmnd=cmnd, dien_thoai=dien_thoai)
        db.session.add(hanh_khach)
        db.session.commit()

        ve = Ve(chuyen_bay_id=chuyen_bay_id, hang_ve=hang_ve, hanh_khach_id=hanh_khach.id)
        db.session.add(ve)
        db.session.commit()

        # Cập nhật lại số lượng ghế hạng 1 và hạng 2
        if hang_ve == 1:
            chuyen_bay.gia_ve_hang_1 -= 1
        else:
            chuyen_bay.gia_ve_hang_2 -= 1

        db.session.commit()

        return redirect(url_for('home'))

    return render_template('ban_ve.html', chuyen_bays=chuyen_bays)



@app.route('/tao_chuyen_bay', methods=['GET', 'POST'])
def tao_chuyen_bay():
    tuyen_bays = TuyenBay.query.all()
    may_bays = MayBay.query.all()
    san_bays = SanBay.query.all()

    if request.method == 'POST':
        ten_chuyen_bay = request.form['ten_chuyen_bay']
        tuyen_bay_id = request.form['tuyen_bay_id']
        may_bay_id = request.form['may_bay_id']
        ngay_gio_bay = datetime.strptime(request.form['ngay_gio_bay'], '%Y-%m-%dT%H:%M')
        thoi_gian_bay = int(request.form['thoi_gian_bay'])
        so_san_bay_tg = int(request.form['so_san_bay_tg'])

        if thoi_gian_bay < 30:
            return "Thời gian bay tối thiểu là 30 phút", 400

        may_bay = MayBay.query.get(may_bay_id)
        so_ghe_hang_1 = may_bay.so_luong_hang_ghe_1
        so_ghe_hang_2 = may_bay.so_luong_hang_ghe_2
        san_bay_trung_gian = []
        thoi_gian_dung = []
        ghi_chu = []

        for i in range(so_san_bay_tg):
            san_bay_trung_gian.append(request.form[f'san_bay_trung_gian{i + 1}'])
            thoi_gian_dung.append(request.form[f'thoi_gian_dung{i + 1}'])
            ghi_chu.append(request.form[f'ghi_chu{i + 1}'])

        if len(san_bay_trung_gian) > 2:
            return "Chỉ được tối đa 2 sân bay trung gian", 400

        for tg in thoi_gian_dung:
            if not 20 <= int(tg) <= 30:
                return "Thời gian dừng phải từ 20-30 phút", 400

        chuyen_bay_moi = ChuyenBay(ten_chuyen_bay=ten_chuyen_bay,
                                   tuyen_bay_id=tuyen_bay_id,
                                   may_bay_id=may_bay_id,
                                   ngay_gio_bay=ngay_gio_bay,
                                   gia_ve_hang_1=so_ghe_hang_1,
                                   gia_ve_hang_2=so_ghe_hang_2)

        db.session.add(chuyen_bay_moi)
        db.session.commit()

        for i, san_bay in enumerate(san_bay_trung_gian):
            if san_bay:
                san_bay_trung_gian_moi = SanBayTrungGian(
                    tuyen_bay_id=tuyen_bay_id,
                    san_bay_id=san_bay,
                    thu_tu_dung=i+1,
                    thoi_gian_dung=int(thoi_gian_dung[i]),
                    ghi_chu=ghi_chu[i]
                )
                db.session.add(san_bay_trung_gian_moi)

        db.session.commit()

        return redirect(url_for('home'))

    return render_template('new_flight.html', tuyen_bays=tuyen_bays, may_bays=may_bays, san_bays=san_bays)


if __name__ == '__main__':
    app.run(debug=True)
