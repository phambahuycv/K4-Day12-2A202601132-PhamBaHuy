# Phiếu Phản Ánh — K4 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: điền câu trả lời bên dưới mỗi câu hỏi.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Phạm Bá Huy  Mã học viên: 2A202601132

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `api_token` không có giá trị mặc định nên app chết ngay khi
khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà việc
"chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Nếu để `api_token` mặc định là `"changeme"`, khi deploy lên production mà kỹ sư quên set biến môi trường `API_TOKEN`, app vẫn khởi động bình thường. Kẻ tấn công hoặc bot tự động trên Internet có thể phát hiện và dùng token mặc định `"changeme"` này để gọi API miễn phí, tiêu tốn hạ tầng và tài chính của ứng dụng mà không bị ngăn chặn. Ngược lại, việc không đặt giá trị mặc định áp dụng nguyên tắc **Fail-fast**: app sẽ ném lỗi `ValidationError` và dừng ngay khi khởi động trên Cloud, giúp kỹ sư phát hiện và bổ sung secret ngay lập tức trước khi traffic rò rỉ ra ngoài.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/chat` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

```json
{"ts": "2026-08-10T16:00:00.123456+00:00", "severity": "INFO", "event": "chat_completed", "client_id": "sv-test", "prompt_tokens": 15, "completion_tokens": 28, "usd_cost": 0.00043, "service": "day12-chat-service", "version": "1.0.0"}
```

1. **Quản lý & Truy vấn tập trung (Log Aggregation & Monitoring)**: Các hệ thống tập trung log (như Datadog, ELK, CloudWatch) tự động parse các trường JSON (`usd_cost`, `prompt_tokens`, `client_id`) để vẽ biểu đồ chi phí thời gian thực hoặc tạo cảnh báo tự động khi một client gọi bất thường.
2. **Truy vết sự cố (Traceability & Auditing)**: Log chuẩn chứa thời gian ISO (`ts`), cấp độ (`severity`), tên dịch vụ (`service`), và phiên bản (`version`), giúp dễ dàng lọc log chính xác theo mốc thời gian hoặc tương quan dữ liệu giữa nhiều container microservices.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t chat:single .
docker build -t chat:multi .
docker images | grep chat
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | ~1.8 GB |
| Multi-stage | ~180 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Phần dung lượng chênh lệch (~1.6 GB) bao gồm:
- Base image đầy đủ (`python:3.11`) chứa toàn bộ bộ biên dịch C/C++ (`gcc`, `g++`), build tools, header files và các gói OS thừa không cần thiết ở môi trường runtime.
- Kỹ thuật Multi-stage tách riêng stage `builder` để biên dịch dependencies, sau đó stage `runtime` chỉ dùng `python:3.11-slim` và copy `/opt/venv` đã cài sang. Điều này giúp loại bỏ toàn bộ compiler, cache và build tools khỏi image cuối cùng.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

- Khi sửa `app/main.py`: Các layer cài đặt thư viện (`COPY requirements.txt .` và `RUN pip install ...`) được **dùng lại hoàn toàn từ Docker cache**, chỉ các layer từ `COPY . .` trở đi mới bị invalid cache và phải chạy lại. Nhờ đó quá trình build diễn ra chỉ trong vài giây.
- Nếu đặt `COPY . .` lên trước `RUN pip install`: Mỗi lần chỉnh sửa mã nguồn Python, cache của `COPY . .` bị vỡ, kéo theo lệnh `RUN pip install` bên dưới bị buộc chạy lại từ đầu, làm tăng đáng kể thời gian build CI/CD.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

- **Chuỗi sự kiện khai thác**:
  1. Code Python dính lỗ hổng (ví dụ RCE hoặc Path Traversal).
  2. Kẻ tấn công gửi payload độc hại để thực thi lệnh shell trong container.
  3. Vì container chạy mặc định dưới user `root` (UID 0), lệnh shell đó có đầy đủ quyền root của container.
  4. Kẻ tấn công lợi dụng lỗ hổng container escape (hoặc mount socket `/var/run/docker.sock`) để thoát ra ngoài máy host.
  5. Vì UID trong container là 0, khi thoát ra máy host, kẻ tấn công chiếm luôn quyền **root của máy host**.
- **Lệnh `USER appuser` cắt đứt ở đâu**: Lệnh `USER` hạ quyền tiến trình xuống user thường không phải root (UID 1000). Khi kẻ tấn công thực thi mã độc trong container, họ chỉ có quyền hạn hạn chế, bị chặn không thể thực hiện các thao tác leo leo quyền hoặc thoát container chiếm máy host.

---

### Câu 6 — Bearer token (CP3)

Vì sao 401 phải kèm header `WWW-Authenticate: Bearer`? Và vì sao ta trả **cùng
một** thông báo lỗi cho cả ba trường hợp (thiếu header, sai scheme, sai token)
thay vì nói rõ sai ở đâu cho người dùng dễ sửa?

- **Vì sao kèm `WWW-Authenticate: Bearer`**: Theo chuẩn HTTP RFC 7235 / RFC 6750, khi trả về HTTP `401 Unauthorized`, server **bắt buộc** phải gửi kèm header `WWW-Authenticate` để chỉ dẫn cho HTTP client biết phương thức xác thực chuẩn mà server yêu cầu (`Bearer`).
- **Vì sao trả cùng một thông báo lỗi**: Đây là nguyên tắc bảo mật phòng thủ (Information Disclosure protection). Nếu trả về lỗi quá chi tiết (*"token không tồn tại"*, *"sai scheme"*, *"token đã hết hạn"*), kẻ tấn công có thể dùng thông tin đó để dò đoán (enumerate) cấu trúc token và phát hiện cơ chế nội bộ của hệ thống.

---

### Câu 7 — Token bucket (CP3)

Với `capacity=10`, `refill_per_minute=10`: một client im lặng 10 phút rồi gửi
liên tiếp. Nó gửi được bao nhiêu request trước khi bị 429? Nếu bỏ đoạn
`min(capacity, ...)` trong `available()` thì con số đó thành bao nhiêu, và tại sao?

- **Số request gửi được trước khi bị 429**: **10 request**. Mặc dù im lặng 10 phút (lý thuyết được 100 token), hàm `available()` có đoạn `min(capacity, ...)` giới hạn số token khả dụng tối đa không vượt quá `capacity = 10`.
- **Nếu bỏ `min(capacity, ...)`**: Con số đó sẽ thành **100 request**. Số token sẽ bị cộng dồn vô hạn ($10 \times 10 = 100$ token). Khi client gửi burst traffic liên tiếp, nó sẽ xả toàn bộ 100 token làm quá tải server, phá hỏng mục đích kiểm soát burst traffic của thuật toán Token Bucket.

---

### Câu 8 — Ngân sách theo ngày (CP3)

So sánh hạn mức $30/tháng với hạn mức $1/ngày cho cùng một client. Giả sử có sự
cố khiến một client gọi liên tục từ 2h sáng. Với mỗi cách, thiệt hại tối đa là
bao nhiêu và service tự hồi phục khi nào?

- **Hạn mức $30/tháng**:
  - *Thiệt hại tối đa*: Lên tới **$30** chỉ trong vài giờ sáng sớm khi client xả hết ngân sách cả tháng.
  - *Thời điểm hồi phục*: Phải chờ tới đầu tháng sau (client có thể bị khóa gần 30 ngày).
- **Hạn mức $1/ngày**:
  - *Thiệt hại tối đa*: Tối đa chỉ **$1**. Khi chạm $1, Cost Guard trả `402 Payment Required` và chặn các request tiếp theo.
  - *Thời điểm hồi phục*: Tự động khôi phục vào 00:00:00 UTC ngày hôm sau (chỉ sau vài giờ).
- **Kết luận**: Hạn mức theo ngày giúp khoanh vùng thiệt hại (blast radius) nhỏ và cho phép tự phục hồi nhanh chóng.

---

### Câu 9 — /healthz khác /readyz (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

1. **0s**: Redis mất kết nối. Cả 3 container đồng loạt trả về 503 ở endpoint gộp.
2. **5s - 15s**: Orchestrator (Docker/Kubernetes) gọi healthcheck thấy fail liên tục $\rightarrow$ lầm tưởng cả 3 container bị crash/deadlock $\rightarrow$ ra lệnh **restart** toàn bộ 3 container.
3. **15s - 30s**: Khi container mới khởi động lại, Redis vẫn chưa có kết nối $\rightarrow$ healthcheck tiếp tục fail $\rightarrow$ container bị restart lại tiếp. Cụm rơi vào vòng lặp restart liên tục (**CrashLoopBackOff / Cascading Failure**), tiêu tốn CPU/RAM và làm sập toàn bộ ứng dụng.
4. **Ý nghĩa tách riêng**: `/healthz` chỉ kiểm tra app process còn sống không (để restart nếu treo), còn `/readyz` mới kiểm tra kết nối Redis (để Load Balancer tạm ngắt traffic khỏi container mà không restart app).

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

- **Thông báo lỗi gặp phải**: `1/1 replicas never became healthy! Healthcheck failed! Path: /healthz` trên Railway.
- **Cách tìm ra nguyên nhân**: Mở Railway Dashboard $\rightarrow$ vào tab *Deployments* $\rightarrow$ kiểm tra *Deploy Logs*. Phát hiện lệnh `startCommand` trong `railway.toml` là `uvicorn app.main:app --host 0.0.0.0 --port $PORT` không được thực thi qua shell handler nên biến `$PORT` không được giải mã, khiến uvicorn bị crash hoặc healthcheck bị timeout.
- **Cách sửa**: Sửa `railway.toml`, bọc `startCommand` trong `sh -c`: `startCommand = "sh -c \"uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}\""` và nâng `healthcheckTimeout` lên `100`. Đồng thời khai báo biến `API_TOKEN` và `REDIS_URL` trên Railway Dashboard.
