<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <span style="font-weight:500">附件</span>
      <el-upload
        :show-file-list="false"
        :before-upload="handleUpload"
        :accept="accept"
      >
        <el-button size="small" :loading="uploading">
          <el-icon><Upload /></el-icon> 上传文件
        </el-button>
      </el-upload>
    </div>

    <div v-if="loading" style="text-align:center;padding:20px">
      <el-icon class="is-loading"><Loading /></el-icon>
    </div>

    <el-empty v-else-if="list.length === 0" description="暂无附件" :image-size="60" />

    <el-table v-else :data="list" size="small">
      <el-table-column label="文件名" min-width="200">
        <template #default="{ row }">
          <el-icon style="margin-right:4px;vertical-align:middle"><component :is="fileIcon(row.mime_type)" /></el-icon>
          <a :href="row.file_url" target="_blank" style="color:#409eff">{{ row.file_name }}</a>
        </template>
      </el-table-column>
      <el-table-column label="大小" width="90">
        <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
      </el-table-column>
      <el-table-column label="上传时间" width="160">
        <template #default="{ row }">{{ row.created_at?.slice(0, 16).replace('T', ' ') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="70" align="center">
        <template #default="{ row }">
          <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAttachments, uploadAttachment, deleteAttachment, type Attachment } from '@/api/attachment'

const props = defineProps<{
  entityType: string
  entityId: string
}>()

const accept = '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.webp'

const list = ref<Attachment[]>([])
const loading = ref(false)
const uploading = ref(false)

async function load() {
  if (!props.entityId) return
  loading.value = true
  try {
    const data = await getAttachments(props.entityType, props.entityId)
    list.value = (data as unknown as { data: Attachment[] }).data ?? (data as unknown as Attachment[])
  } finally {
    loading.value = false
  }
}

watch(() => props.entityId, load, { immediate: true })

async function handleUpload(file: File) {
  uploading.value = true
  try {
    await uploadAttachment(props.entityType, props.entityId, file)
    ElMessage.success('上传成功')
    await load()
  } catch {
    // 错误已由 axios 拦截器统一处理
  } finally {
    uploading.value = false
  }
  return false // 阻止 el-upload 自动上传
}

async function handleDelete(row: Attachment) {
  await ElMessageBox.confirm(`确定删除「${row.file_name}」？`, '提示', { type: 'warning' })
  await deleteAttachment(row.id)
  ElMessage.success('已删除')
  list.value = list.value.filter(a => a.id !== row.id)
}

function fileIcon(mime: string | null) {
  if (!mime) return 'Document'
  if (mime.startsWith('image/')) return 'Picture'
  if (mime.includes('pdf')) return 'Document'
  if (mime.includes('sheet') || mime.includes('excel')) return 'Grid'
  return 'Document'
}

function formatSize(bytes: number | null) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}
</script>
