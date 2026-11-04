# 哈希源目录

把第三方 SHA256 清单放到这里（`*.json`），然后执行：

```bash
python scripts/update_hashes.py --rebuild
```

也可不重建：`scan.py` 启动时会直接合并本目录下全部 JSON。

## JSON 格式

```json
{
  "malicious_hashes": [
    {
      "sha256": "64位十六进制",
      "name": "样本名",
      "description": "可选说明"
    }
  ]
}
```

也接受 `{"malicious_hashes": {"<sha256>": "名称"}}`。

不要把恶意样本本体放进本目录，只放哈希。
