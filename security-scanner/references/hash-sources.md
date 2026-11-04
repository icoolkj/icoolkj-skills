# 哈希源

第三方 SHA256 清单支持两种放置方式，扫描与重建时自动合并（后者覆盖内置库与 `hashes.json`）：

1. **平铺单文件（推荐，平台分发兼容）**：`references/hash-sources.json`
2. **目录方式（仅本地开发使用）**：`references/hash-sources/*.json`，目录不存在时自动跳过

> 注意：Skill 包仅支持两级目录结构（根目录/二级目录/文件），因此打包分发时只能使用平铺单文件方式，不要创建三级目录。

放置后可执行重建合并进主库：

```bash
python scripts/update_hashes.py --rebuild
```

也可不重建：`scan.py` 启动时会直接合并以上全部 JSON。

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

不要把恶意样本本体放进仓库，只放哈希。
