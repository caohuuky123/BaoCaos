from datetime import datetime
from BaoCaos.QuanLyChuyenBay import app, dao, admin, login, utils
from flask import render_template, request, redirect, session, jsonify, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
import cloudinary.uploader
from BaoCaos.QuanLyChuyenBay import app, dao, db, gio_mua_toi_da, gio_ban_toi_da, thoi_gian_bay_toi_thieu, \
    san_bay_trung_gian_toi_da, thoi_gian_dung_toi_da, thoi_gian_dung_toi_thieu
from BaoCaos.QuanLyChuyenBay.models import LichChuyenBay, san_bay_trung_gian, QuyDinh, ChuyenBay, SanBay
from flask import render_template
import json
import uuid
import requests
import hmac
import hashlib


@app.route('/')
def home():
    san_bay = dao.load_san_bay()
    Tu = request.args.get("from")
    Den = request.args.get("to")
    Ngay = request.args.get("date")
    lich_chuyen_bay = dao.load_lich_may_bay(Tu, Den, Ngay)
    chuyen_bay = dao.load_chuyen_bay()

    now = datetime.now()
    ve = dao.load_ve()
    return render_template('index.html', lich_chuyen_bay=lich_chuyen_bay, chuyen_bay=chuyen_bay, ve=ve, now=now, san_bay=san_bay)

###### Thêm lịch chuyến bay
@app.route('/AddFlightSchedule', methods=['get', 'post'])
def AddFlightSchedule():
    currentDay = datetime.now().day
    currentMonth = datetime.now().month
    currentYear = datetime.now().year
    now = f"{currentYear}-{currentMonth}-{currentDay}"
    ero_msg = ''
    success_msg = ''
    chuyen_bay = dao.load_chuyen_bay()
    may_bay = dao.load_may_bay()
    san_bay = dao.load_san_bay()
    if request.method.__eq__("POST"):
        image = request.form['image']
        chuyen_bay_id = request.form['chuyen_bay']
        may_bay_id = request.form['may_bay']
        ngay_khoi_hanh = request.form['ngay_khoi_hanh']
        thoi_gian_bay = request.form['thoi_gian_bay']
        san_bay_di = request.form['san_bay_di']
        san_bay_den = request.form['san_bay_den']
        price = request.form['price']
        soluongh1 = request.form['soluongh1']
        soluongh2 = request.form['soluongh2']
        so_sbtg = request.form['so_san_bay_tg']
        san_bay_trung_gian_list = []
        thoi_gian_dung_list = []
        ghi_chu_list = []

        for i in range(int(float(so_sbtg))):
            san_bay_trung_gian_list.append(request.form['san_bay_trung_gian' + str(i + 1)])
            thoi_gian_dung_list.append(request.form['thoi_gian_dung' + str(i + 1)])
            ghi_chu_list.append(request.form['ghi_chu' + str(i + 1)])
        result = dao.checkIfDuplicates(san_bay_trung_gian_list)
        copy_list = [float(i) for i in thoi_gian_dung_list]
        thoi_gian_cho = sum(copy_list)
        if dao.get_san_bay_by_id((dao.get_chuyen_bay_by_id(chuyen_bay_id).san_bay_di_id)).dia_diem \
                != dao.get_san_bay_by_id(san_bay_di).dia_diem:
            ero_msg = 'Sân bay đi không hợp lệ với chuyến bay đã chọn'
        if dao.get_san_bay_by_id((dao.get_chuyen_bay_by_id(chuyen_bay_id).san_bay_den_id)).dia_diem \
                != dao.get_san_bay_by_id(san_bay_den).dia_diem:
            ero_msg = 'Sân bay đến không hợp lệ với chuyến bay đã chọn'
        if dao.get_san_bay_by_id(san_bay_den) == dao.get_san_bay_by_id(san_bay_di):
            ero_msg = 'Sân bay đi và đến không thể trùng nhau'
        if int(soluongh1) + int(soluongh2) > dao.get_may_bay_by_id(may_bay_id).so_luong_cho_ngoi:
            ero_msg = 'Tổng số lượng hạng vé vượt quá sức chứa máy bay'
        if result:
            ero_msg = 'Sân bay trung gian nhập trùng nhau'
        if thoi_gian_cho >= float(thoi_gian_bay):
            ero_msg = 'Thời gian chờ không thể lớn hơn thời gian bay'
        if san_bay_den in san_bay_trung_gian_list or san_bay_di in san_bay_trung_gian_list:
            ero_msg = 'Sân bay trung gian trùng với sân bay đi hoặc đến'
        if ero_msg != '':
            return render_template('AddFlightSchedule.html', chuyen_bay=chuyen_bay, may_bay=may_bay, san_bay=san_bay,
                                   now=now, ero_msg=ero_msg)
        else:
            l = LichChuyenBay(chuyen_bay_id=chuyen_bay_id, ngay_gio=ngay_khoi_hanh, thoi_gian_bay=thoi_gian_bay,
                              so_luong_hang_ve_1=soluongh1,
                              so_luong_hang_ve_2=soluongh2, price=price, image=image, may_bay_id=may_bay_id)
            db.session.add(l)

            try:
                db.session.commit()
                for i in range(len(san_bay_trung_gian_list)):
                    query = san_bay_trung_gian.insert().values(lich_chuyen_bay_id=l.id,
                                                               san_bay=san_bay_trung_gian_list[i],
                                                               thoi_gian_dung=thoi_gian_dung_list[i],
                                                               ghi_chu=ghi_chu_list[i])
                    db.engine.execute(query)
                success_msg = "Đã thêm lịch chuyến bay thành công!"
            except:
                ero_msg = 'Hệ thống đang lỗi!!! thử lại sau'
            else:
                return render_template('AddFlightSchedule.html', chuyen_bay=chuyen_bay, may_bay=may_bay, san_bay=san_bay,
                                       now=now, success_msg=success_msg)
    return render_template('AddFlightSchedule.html',
                           chuyen_bay=chuyen_bay,
                           may_bay=may_bay,
                           san_bay=san_bay,
                           now=now,
                           ero_msg=ero_msg,
                           success_msg=success_msg)


@app.route('/login-admin', methods=['post'])
def admin_login():
    username = request.form['username']
    password = request.form['password']
    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)

    return redirect('/admin')


@app.route('/login', methods=['get', 'post'])
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
            err_msg = ' Tên đăng nhập hoặc Mật khẩu không chính xác !!!'
    return render_template('login.html', err_msg=err_msg)


@app.route('/register', methods=['get', 'post'])
def user_register():
    err_msg = ''
    if request.method.__eq__('POST'):
        password = request.form['password']
        confirm = request.form['confirm']
        if password.__eq__(confirm):
            avatar = ''
            if request.files:
                res = cloudinary.uploader.upload(request.files['avatar'])
                avatar = res['secure_url']

            try:
                dao.register(name=request.form['name'],
                             username=request.form['username'],
                             password=password, avatar=avatar)
                return redirect('/login')
            except:
                err_msg = 'Hệ thống đang lỗi. Vui lòng thử lại sau !!'
        else:
            err_msg = 'Mật khẩu KHÔNG khớp!'

    return render_template('register.html', err_msg=err_msg)


@app.route('/logout')
def logout_my_user():
    logout_user()
    return redirect('/login')


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)

######## qui dinh
@app.route("/RuleChange", methods=['GET', 'POST'])
def RuleChange():
    quy_dinh_list = QuyDinh.query.all()
    msg = ""

    if request.method == 'POST':
        if 'add_rule' in request.form:  # Thêm quy định mới
            try:
                tg_bay_toi_thieu = float(request.form['thoi_gian_bay'])
                sbtg_toi_da = int(request.form['sbtg_toi_da'])
                tg_dung_toi_thieu = float(request.form['thoi_gian_dung_toi_thieu'])
                tg_dung_toi_da = float(request.form['thoi_gian_dung_toi_da'])
                thoi_gian_ban = float(request.form['thoi_gian_ban'])
                thoi_gian_mua = float(request.form['thoi_gian_mua'])

                # Số lượng và đơn giá hạng vé
                h1_seat_count = int(request.form['h1_seat_count'])
                h2_seat_count = int(request.form['h2_seat_count'])
                h1_price = float(request.form['h1_price'])
                h2_price = float(request.form['h2_price'])

                # Lưu quy định mới vào cơ sở dữ liệu
                new_rule = QuyDinh(
                    thoi_gian_bay_toi_thieu=tg_bay_toi_thieu,
                    sbtg_toi_da=sbtg_toi_da,
                    thoi_gian_dung_toi_thieu=tg_dung_toi_thieu,
                    thoi_gian_dung_toi_da=tg_dung_toi_da,
                    thoi_gian_ban=thoi_gian_ban,
                    thoi_gian_mua=thoi_gian_mua,
                    h1_seat_count=h1_seat_count,
                    h2_seat_count=h2_seat_count,
                    h1_price=h1_price,
                    h2_price=h2_price
                )
                db.session.add(new_rule)
                db.session.commit()
                msg = "Thêm quy định mới thành công!"
            except Exception as e:
                db.session.rollback()
                msg = f"Lỗi khi thêm quy định: {e}"

    return render_template("RuleChange.html", quy_dinh_list=quy_dinh_list, msg=msg)

#Chinh sua va xoa qui dinh
@app.route("/delete_rule/<int:id>", methods=['GET'])
def delete_rule(id):
    try:
        quy_dinh_to_delete = QuyDinh.query.get(id)
        if quy_dinh_to_delete:
            db.session.delete(quy_dinh_to_delete)
            db.session.commit()
            flash("Quy định đã được xóa thành công!", "success")
        else:
            flash("Quy định không tồn tại!", "error")
    except Exception as e:
        db.session.rollback()
        flash("Đã xảy ra lỗi khi xóa quy định!", "error")
    return redirect(url_for('RuleChange'))  # Thay thế 'show_rules' bằng 'RuleChange'

@app.route("/edit_rule", methods=['POST'])
def edit_rule():
    try:
        quy_dinh_id = request.form.get('edit_id')
        quy_dinh_to_edit = QuyDinh.query.get(quy_dinh_id)
        if quy_dinh_to_edit:
            quy_dinh_to_edit.thoi_gian_bay_toi_thieu = request.form['thoi_gian_bay']
            quy_dinh_to_edit.sbtg_toi_da = request.form['sbtg_toi_da']
            quy_dinh_to_edit.thoi_gian_dung_toi_thieu = request.form['thoi_gian_dung_toi_thieu']
            quy_dinh_to_edit.thoi_gian_dung_toi_da = request.form['thoi_gian_dung_toi_da']
            quy_dinh_to_edit.thoi_gian_ban = request.form['thoi_gian_ban']
            quy_dinh_to_edit.thoi_gian_mua = request.form['thoi_gian_mua']
            quy_dinh_to_edit.h1_seat_count = request.form['h1_seat_count']
            quy_dinh_to_edit.h2_seat_count = request.form['h2_seat_count']
            quy_dinh_to_edit.h1_price = request.form['h1_price']
            quy_dinh_to_edit.h2_price = request.form['h2_price']
            db.session.commit()
            flash("Cập nhật quy định thành công!", "success")
        else:
            flash("Quy định không tồn tại!", "error")
    except Exception as e:
        db.session.rollback()
        flash("Đã xảy ra lỗi khi cập nhật quy định!", "error")
    return redirect(url_for('show_rules'))

@app.route('/lich_chuyen_bay/<int:lich_chuyen_bay_id>')
def details(lich_chuyen_bay_id):
    lcb = dao.chi_tiet_chuyen_bay(lich_chuyen_bay_id)
    cb = dao.load_chuyen_bay()
    mb = dao.load_may_bay()
    sb = dao.load_san_bay()
    sbtg = dao.load_sbtg(lich_chuyen_bay_id)
    return render_template('details.html', lich_chuyen_bay=lcb, chuyen_bay=cb, may_bay=mb, san_bay=sb,
                           san_bay_trung_gian=sbtg, dao=dao)

###Them sua xoa chuyen bay
@app.route('/flight_management')
def flight_management():
    # Lấy tất cả các chuyến bay từ cơ sở dữ liệu
    flight_list = ChuyenBay.query.all()
    return render_template('your_template.html', flight_list=flight_list)


# Route Thêm Chuyến Bay
@app.route("/add_flight", methods=['GET', 'POST'])
def add_flight():
    if request.method == 'POST':
        ten_chuyen_bay = request.form['ten_chuyen_bay']
        san_bay_di_id = request.form['san_bay_di_id']
        san_bay_den_id = request.form['san_bay_den_id']
        new_flight = ChuyenBay(
            ten_chuyen_bay=ten_chuyen_bay,
            san_bay_di_id=san_bay_di_id,
            san_bay_den_id=san_bay_den_id
        )
        db.session.add(new_flight)
        db.session.commit()
        return redirect(url_for('flight_management'))

    san_bays = SanBay.query.all()
    return render_template('add_flight.html', san_bays=san_bays)


# Route Xóa Chuyến Bay
@app.route("/delete_flight/<int:id>", methods=['GET', 'POST'])
def delete_flight(id):
    flight = ChuyenBay.query.get(id)
    if flight:
        db.session.delete(flight)
        db.session.commit()
    return redirect(url_for('flight_management'))

if __name__ == '__main__':
    app.run(debug=True)
@app.route("/order")
def order():
    san_bay = dao.load_san_bay()
    Tu = request.args.get("from")
    Den = request.args.get("to")
    Ngay = request.args.get("date")
    lich_chuyen_bay = dao.load_lich_may_bay(Tu, Den, Ngay)
    chuyen_bay = dao.load_chuyen_bay()
    now = datetime.now()
    ve = dao.load_ve()
    return render_template('order.html', lich_chuyen_bay=lich_chuyen_bay, chuyen_bay=chuyen_bay, ve=ve, now=now,
                           san_bay=san_bay)
@app.route("/result")
def result():
    Tu = request.args.get("from")
    Den = request.args.get("to")
    sove = int(request.args.get("Soluongve"))
    lich_chuyen_bay = dao.load_lich_may_bay(Tu, Den)
    chuyen_bay = dao.load_chuyen_bay()
    now = datetime.now()
    return render_template("result.html", lich_chuyen_bay=lich_chuyen_bay, chuyen_bay=chuyen_bay, sove=sove, now=now)


@app.route("/cus_information/<int:lich_chuyen_bay_id>&<sove>")
def addinformation(lich_chuyen_bay_id, sove):
    cb = dao.load_chuyen_bay()
    lich_chuyen_bay = dao.chi_tiet_chuyen_bay(lich_chuyen_bay_id)
    return render_template("cus_information.html", sove=int(sove), chuyen_bay_id=lich_chuyen_bay_id, cb=cb,
                           lich_chuyen_bay=lich_chuyen_bay)


@app.route('/cus_information/<int:sove>')
def addcus(sove):
    cb = dao.load_chuyen_bay()
    return render_template("cus_information.html", sove=sove, cb=cb)


@app.route('/cus_information_cart/<int:sove>')
def add_cus_by_cart(sove):
    cb = dao.load_chuyen_bay()
    return render_template("cus_information_cart.html", sove=sove, cb=cb)


@app.route('/cus_information/chuyen_bay_<int:chuyen_bay_id>')
def cus(chuyen_bay_id):
    cb = dao.load_chuyen_bay()
    sove = request.args.get("Soluongve")
    lich_chuyen_bay = dao.chi_tiet_chuyen_bay(chuyen_bay_id)
    tongtien = int(lich_chuyen_bay.price) * int(sove)
    return render_template("cus_information.html", sove=int(sove), cb=cb, chuyen_bay_id=chuyen_bay_id,
                           lich_chuyen_bay=lich_chuyen_bay, tongtien=tongtien)


@app.route('/cart')
def cart():
    cb = dao.load_chuyen_bay()
    if current_user.is_authenticated:
        now = datetime.now()
        ticket = dao.ticket_of_user(current_user.id)
        return render_template('cart.html', cb=cb, ticket=ticket, dao=dao, now=now)
    return render_template('cart.html', cb=cb)


@app.route('/api/cart', methods=['post'])
def add_to_cart():
    data = request.json
    id = str(data['id'])
    chuyen_bay_id = data['chuyen_bay_id']
    price = data['price']

    key = app.config['CART_KEY']
    cart = session.get(key, {})

    if id in cart:
        cart[id]['quantity'] += 1
    else:
        cart[id] = {
            "id": id,
            "chuyen_bay_id": chuyen_bay_id,
            "price": price,
            "quantity": 1
        }

    session[key] = cart

    return jsonify(utils.cart_stats(cart))


@app.route('/api/cart/<lich_chuyen_bay_id>', methods=['put'])
def updateCart(lich_chuyen_bay_id):
    key = app.config['CART_KEY']
    cart = session.get(key)

    if cart and lich_chuyen_bay_id in cart:
        quantity = int(request.json['quantity'])
        cart[lich_chuyen_bay_id]['quantity'] = quantity

    session[key] = cart
    return jsonify(utils.cart_stats(cart))


@app.route('/api/cart/<lich_chuyen_bay_id>', methods=['delete'])
def delete_cart(lich_chuyen_bay_id):
    key = app.config['CART_KEY']
    cart = session.get(key)

    if cart and lich_chuyen_bay_id in cart:
        del cart[lich_chuyen_bay_id]

    session[key] = cart
    return jsonify(utils.cart_stats(cart))


@app.context_processor
def common_atttributes():
    return {
        'cart': utils.cart_stats(session.get(app.config['CART_KEY'])),
        'gio_mua_toi_da': gio_mua_toi_da,
        'gio_ban_toi_da': gio_ban_toi_da,
        'thoi_gian_bay_toi_thieu': thoi_gian_bay_toi_thieu,
        'san_bay_trung_gian_toi_da': san_bay_trung_gian_toi_da,
        'thoi_gian_dung_toi_da': thoi_gian_dung_toi_da,
        'thoi_gian_dung_toi_thieu': thoi_gian_dung_toi_thieu
    }


# pay, cho ng dung thanh toan online
@app.route('/api/pay/<int:sove>', methods=['post'])
@login_required
def pay(sove):
    money = request.form['total']
    key = app.config['CART_KEY']
    cart = session.get(key)
    if cart and dao.save_ticket(cart, sove):
        del session[key]
    else:
        return redirect("/")
        # return jsonify({'status': 500})
    total = str(int(float(money)))
    return redirect("/")
    # return jsonify({'status': 200})
    # return redirect(dao.MoMo(total))


# paynow cho nhan vien ban tại cho
@app.route('/api/pay/chuyen_bay_<int:chuyen_bay_id>&so_ve<int:sove>', methods=['post'])
@login_required
def pay_now(sove, chuyen_bay_id):
    money = request.form['total']
    if dao.save_ticket_now(sove, chuyen_bay_id):
        pass
    else:
        return render_template("test.html", ero='Thanh toán không  thành công')
    total = str(int(float(money)))
    # return jsonify({'status': 200})
    return redirect("/")


    # return redirect(dao.MoMo(total))


if __name__ == '__main__':
    app.run(debug=True)
