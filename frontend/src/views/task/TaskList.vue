<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { taskApi, projectApi, type TaskListItem, type ProjectListItem } from '@/api/project'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()

const loading = ref(false)
const list = ref<TaskListItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '', keyword: '' })

const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  project_id: '',
  task_name: '',
  task_type: '文件审查',
  description: '',
  assigned_to: '',
  priority: '普通',
  planned_start: '',
  planned_end: '',
  status: '待开始',
})
const editId = ref<string | null>(null)
const saving = ref(false)

const statusOptions = ['待开始', '进行中', '已完成', '已取消']
const taskTypeOptions = ['文件审查', '现场审核', '报告编写', '其他']
const priorityOptions = ['紧急', '高', '普通', '低']

// 项目搜索
const projectOptions = ref<ProjectListItem[]>([])
const projectLoading = ref(false)
async function searchProjects(keyword: string) {
  if (!keyword) return
  projectLoading.value = true
  try {
    const res = await projectApi.list({ keyword, page_size: 20 })
    projectOptions.value = res.data
  } finally {
    projectLoading.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    const res = await taskApi.list(params as any)
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() { query.status = ''; query.keyword = ''; query.page = 1; loadList() }

function openCreate() {
  editId.value = null
  projectOptions.value = []
  Object.assign(form, {
    project_id: '', task_name: '', task_type: '文件审查', description: '',
    assigned_to: authStore.user?.id ?? '', priority: '普通',
    planned_start: '', planned_end: '', status: '待开始',
  })
  dialogVisible.value = true
}

async function openEdit(row: TaskListItem) {
  editId.value = row.id
  const pRes = await projectApi.list({ keyword: '', page_size: 50 })
  projectOptions.value = pRes.data
  Object.assign(form, {
    project_id: row.project_id,
    task_name: row.task_name,
    task_type: row.task_type,
    description: '',
    assigned_to: row.assigned_to,
    priority: row.priority,
    planned_start: row.planned_start,
    planned_end: row.planned_end,
    status: row.status,
  })
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload: Record<string, unknown> = { ...form }
    if (editId.value) {
      await taskApi.update(editId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await taskApi.create(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: TaskListItem) {
  await ElMessageBox.confirm(`确认删除任务「${row.task_name}」？`, '提示', { type: 'warning' })
  await taskApi.delete(row.id)
  ElMessage.success('已删除')
  loadList()
}

async function quickStatus(row: TaskListItem, status: string) {
  await taskApi.update(row.id, { status })
  row.status = status
  ElMessage.success('状态已更新')
}

const statusTagType = (s: string) =>
  ({ '待开始': 'info', '进行中': 'primary', '已完成': 'success', '已取消': 'danger' }[s] ?? '') as any

const priorityTagType = (p: string) =>
  ({ '紧急': 'danger', '高': 'warning', '普通': '', '低': 'info' }[p] ?? '') as any

function fmtDt(dt: string) {
  return dt ? dt.slice(0, 10) : '-'
}

onMounted(loadList)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="7">
          <el-input v-model="query.keyword" placeholder="搜索任务名称" clearable @keyup.enter="handleSearch" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="query.status" placeholder="状态" clearable style="width:100%">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
        <el-col :span="8" style="text-align:right">
          <el-button type="primary" icon="Plus" @click="openCreate">新建任务</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id">
        <el-table-column prop="task_name" label="任务名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="task_type" label="类型" width="100" />
        <el-table-column label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="priorityTagType(row.priority)" size="small">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="计划开始" width="110">
          <template #default="{ row }">{{ fmtDt(row.planned_start) }}</template>
        </el-table-column>
        <el-table-column label="计划完成" width="110">
          <template #default="{ row }">{{ fmtDt(row.planned_end) }}</template>
        </el-table-column>
        <el-table-column label="实际完成" width="110">
          <template #default="{ row }">{{ fmtDt(row.actual_end) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-dropdown @command="(s: string) => quickStatus(row, s)">
              <el-tag :type="statusTagType(row.status)" size="small" style="cursor:pointer">
                {{ row.status }} <el-icon style="margin-left:2px"><ArrowDown /></el-icon>
              </el-tag>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-for="s in statusOptions" :key="s" :command="s">{{ s }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top:16px;justify-content:flex-end;display:flex"
        @change="loadList"
      />
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑任务' : '新建审核任务'" width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" label-width="80px" :rules="{
        project_id: [{ required: true, message: '请选择关联项目' }],
        task_name: [{ required: true, message: '请输入任务名称' }],
        planned_start: [{ required: true, message: '请选择计划开始时间' }],
        planned_end: [{ required: true, message: '请选择计划完成时间' }],
      }">
        <el-row :gutter="16">
          <el-col :span="24">
            <el-form-item label="关联项目" prop="project_id">
              <el-select
                v-model="form.project_id"
                filterable remote
                :remote-method="searchProjects"
                :loading="projectLoading"
                placeholder="输入项目编号/标准搜索"
                style="width:100%"
              >
                <el-option
                  v-for="p in projectOptions"
                  :key="p.id"
                  :label="`${p.project_no} ${p.standard}`"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="任务名称" prop="task_name">
              <el-input v-model="form.task_name" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="优先级">
              <el-select v-model="form.priority" style="width:100%">
                <el-option v-for="p in priorityOptions" :key="p" :label="p" :value="p" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务类型">
              <el-select v-model="form.task_type" style="width:100%">
                <el-option v-for="t in taskTypeOptions" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%">
                <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划开始" prop="planned_start">
              <el-date-picker v-model="form.planned_start" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划完成" prop="planned_end">
              <el-date-picker v-model="form.planned_end" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
