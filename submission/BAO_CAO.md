# Báo cáo ngắn – Day21 Track2: CI/CD cho AI Systems

## 1) Bộ siêu tham số đã chọn (kết quả Bước 1) và lý do

- **Mô hình**: `RandomForestClassifier`
- **Bộ siêu tham số lựa chọn cuối cùng**:

```yaml
n_estimators: 2000
max_depth: null
min_samples_split: 2
```

- **Lý do chọn**:
  - Trong quá trình thử nghiệm nhiều cấu hình khác nhau và theo dõi kết quả, cấu hình trên cho **accuracy cao nhất trong các lần thử** (xấp xỉ **~0.68**).
  - So với cấu hình như `n_estimators: 500, max_depth: 10, min_samples_split: 2` (accuracy khoảng **~0.648**), việc tăng `n_estimators` và để `max_depth: null` giúp mô hình học tốt hơn và cải thiện kết quả trên tập đánh giá.
  - Cấu hình này được dùng làm baseline để chạy pipeline huấn luyện/tự động hoá ở Bước 2.

## 2) Khó khăn gặp phải và cách giải quyết

- **MLflow UI không hiển thị run / lỗi khi log artifact**
  - **Nguyên nhân**: cấu hình tracking/artifact chưa đồng bộ khi dùng SQLite local; một số trường hợp UI bị filter hoặc artifact URI không phù hợp.
  - **Giải pháp**: cấu hình lại tracking dùng `sqlite:///mlflow.db`, đảm bảo artifact root local (`./mlartifacts`), chạy lại train và mở MLflow UI để so sánh các run theo `accuracy`.

- **DVC push lên S3 gặp lỗi `AccessDenied`**
  - **Nguyên nhân**: thiếu quyền S3 hoặc DVC không dùng đúng chain credential/profile/region.
  - **Giải pháp**: tạo bucket S3, cấu hình DVC remote `s3://<bucket>/dvc`, đảm bảo region đúng (`ap-southeast-1`), điều chỉnh cấu hình remote (profile/region), kiểm tra quyền bằng AWS CLI và thực hiện lại `dvc push` thành công (xác nhận object xuất hiện dưới prefix `dvc/`).

- **Không SSH được vào EC2 trên Windows do lỗi quyền file `.pem`**
  - **Nguyên nhân**: OpenSSH yêu cầu private key không được “too open” (ACL Windows cho phép nhiều user đọc).
  - **Giải pháp**: siết quyền file key bằng `icacls` (loại bỏ `Authenticated Users/Users`, chỉ để user hiện tại đọc), sau đó SSH vào EC2 thành công.

- **Cài package Python trên Ubuntu báo `externally-managed-environment` (PEP 668)**
  - **Nguyên nhân**: Ubuntu mới chặn cài pip trực tiếp vào môi trường Python hệ thống.
  - **Giải pháp**: tạo virtual environment `mlops-venv`, activate và cài các package (`fastapi`, `uvicorn`, `boto3`, `scikit-learn`, `joblib`) trong venv.

- **Service inference crash do thiếu model trên S3 (404 Not Found)**
  - **Nguyên nhân**: `serve.py` tải model từ `s3://<bucket>/models/latest/model.pkl` nhưng object chưa tồn tại.
  - **Giải pháp**: upload model lên đúng key trên S3, restart systemd service; kiểm tra thành công qua `GET /health` và `POST /predict`.

## Kết luận

Sau khi hoàn tất Bước 1 (thử nghiệm/tuning và chọn siêu tham số), hệ thống đã sẵn sàng cho Bước 2: dữ liệu được quản lý bằng DVC trên S3, VM (EC2) chạy inference qua systemd, và pipeline CI/CD có thể triển khai tự động khi đạt ngưỡng chất lượng.

