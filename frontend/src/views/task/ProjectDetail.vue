<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectApi, taskApi, type ProjectOut, type TaskOut } from '@/api/project'
import AttachmentPanel from '@/components/common/AttachmentPanel.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string

const project = ref<ProjectOut | null>(null)
const tasks = ref<TaskOut[]>([])
const loading = ref(false)

// 任务表单
const taskDialogVisible = ref(false)
const taskFormRef = ref()
const taskForm = ref({
  task_name: '',
  task_type: '文件审查',
  description: '',
  assigned_to: '',
  priority: '普通',
  planned_start: '',
  planned_end: '',
  status: '待开始',
})
const editTaskId = ref<string | null>(null)
const taskSaving = ref(false)

const taskTypeOptions = ['文件审查', '现场审核', '报告编写', '其他']
const priorityOptions = ['紧急', '高', '普通', '低']
const taskStatusOptions = ['待开始', '进行中', '已完成', '已取消']

async function load() {
  loading.value = true
  try {
    const [pRes, tRes] = await Promise.all([
      projectApi.get(projectId),
      projectApi.listTasks(projectId),
    ])
    project.value = pRes.data
    tasks.value = tRes.data
  } finally {
    loading.value = false
  }
}

function openCreateTask() {
  editTaskId.value = null
  Object.assign(taskForm.value, {
    task_name: '', task_type: '文件审查', description: '',
    assigned_to: '', priority: '普通',
    planned_start: '', planned_end: '', status: '待开始',
  })
  taskDialogVisible.value = true
}

function openEditTask(row: TaskOut) {
  editTaskId.value = row.id
  Object.assign(taskForm.value, {
    task_name: row.task_name,
    task_type: row.task_type,
    description: row.description ?? '',
    assigned_to: String(row.assigned_to),
    priority: row.priority,
    planned_start: row.planned_start?.slice(0, 16) ?? '',
    planned_end: row.planned_end?.slice(0, 16) ?? '',
    status: row.status,
  })
  taskDialogVisible.value = true
}

async function handleTaskSave() {
  await taskFormRef.value?.validate()
  taskSaving.value = true
  try {
    const payload: Record<string, unknown> = { ...taskForm.value }
    if (editTaskId.value) {
      await taskApi.update(editTaskId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await taskApi.create({ ...payload, project_id: projectId })
      ElMessage.success('创建成功')
    }
    taskDialogVisible.value = false
    await load()
  } finally {
    taskSaving.value = false
  }
}

async function handleDeleteTask(row: TaskOut) {
  await ElMessageBox.confirm(`确认删除任务「${row.task_name}」？`, '提示', { type: 'warning' })
  await taskApi.delete(row.id)
  ElMessage.success('已删除')
  tasks.value = tasks.value.filter(t => t.id !== row.id)
}

const projectStatusTagType = (s: string) =>
  ({ '筹备中': 'info', '进行中': 'primary', '已完成': 'success', '已取消': 'danger' }[s] ?? '') as any

const taskStatusTagType = (s: string) =>
  ({ '待开始': 'info', '进行中': 'primary', '已完成': 'success', '已取消': 'danger' }[s] ?? '') as any

const priorityTagType = (s: string) =>
  ({ '紧急': 'danger', '高': 'warning', '普通': '', '低': 'info' }[s] ?? '') as any

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <el-page-header @back="router.back()" style="margin-bottom:16px">
      <template #content>
        <span>{{ project?.project_no }} - {{ project?.standard }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="16">
      <!-- 左侧：项目信息 + 附件 -->
      <el-col :span="16">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><span>项目基本信息</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="项目编号">{{ project?.project_no }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="projectStatusTagType(project?.status ?? '')" size="small">{{ project?.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="认证标准" :span="2">{{ project?.standard }}</el-descriptions-item>
            <el-descriptions-item label="认证范围" :span="2">{{ project?.certification_scope }}</el-descriptions-item>
            <el-descriptions-item label="阶段">{{ project?.phase }}</el-descriptions-item>
            <el-descriptions-item label="进度">
              <el-progress :percentage="project?.progress ?? 0" :stroke-width="8" style="width:160px" />
            </el-descriptions-item>
            <el-descriptions-item label="计划开始">{{ project?.planned_start_date ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="计划完成">{{ project?.planned_end_date ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="实际完成">{{ project?.actual_end_date ?? '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never">
          <AttachmentPanel entity-type="cert_project" :entity-id="projectId" />
        </el-card>
      </el-col>

      <!-- 右侧：任务列表 -->
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>审核任务</span>
              <el-button size="small" type="primary" icon="Plus" @click="openCreateTask">新建任务</el-button>
            </div>
          </template>

          <div v-if="tasks.length === 0" style="color:#c0c4cc;text-align:center;padding:20px 0;font-size:13px">
            暂无任务
          </div>

          <div v-for="task in tasks" :key="task.id"
            style="padding:10px 0;border-bottom:1px solid #f5f5f5">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div style="flex:1;min-width:0">
                <div style="font-size:13px;font-weight:500;margin-bottom:4px">{{ task.task_name }}</div>
                <div style="font-size:12px;color:#909399">
                  <el-tag size="small" style="margin-right:4px">{{ task.task_type }}</el-tag>
                  <el-tag :type="priorityTagType(task.priority)" size="small" style="margin-right:4px">{{ task.priority }}</el-tag>
                  <el-tag :type="taskStatusTagType(task.status)" size="small">{{ task.status }}</el-tag>
                </div>
                <div style="font-size:12px;color:#c0c4cc;margin-top:4px">
                  {{ task.planned_end?.slice(0, 10) }} 截止
                </div>
              </div>
              <div style="flex-shrink:0;margin-left:8px">
                <el-button link size="small" type="primary" @click="openEditTask(task)">编辑</el-button>
                <el-button link size="small" type="danger" @click="handleDeleteTask(task)">删除</el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务编辑弹窗 -->
    <el-dialog v-model="taskDialogVisible" :title="editTaskId ? '编辑任务' : '新建任务'" width="500px" destroy-on-close>
      <el-form ref="taskFormRef" :model="taskForm" label-width="80px" :rules="{
        task_name: [{ required: true, message: '请输入任务名称' }],
        assigned_to: [{ required: true, message: '请填写负责人' }],
        planned_start: [{ required: true, message: '请选择计划开始时间' }],
        planned_end: [{ required: true, message: '请选择计划结束时间' }],
      }">
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="taskForm.task_name" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="类型">
              <el-select v-model="taskForm.task_type" style="width:100%">
                <el-option v-for="t in taskTypeOptions" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="taskForm.priority" style="width:100%">
                <el-option v-for="p in priorityOptions" :key="p" :label="p" :value="p" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="负责人ID" prop="assigned_to">
          <el-input v-model="taskForm.assigned_to" placeholder="用户 UUID" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="计划开始" prop="planned_start">
              <el-date-picker v-model="taskForm.planned_start" type="datetime"
                value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划结束" prop="planned_end">
              <el-date-picker v-model="taskForm.planned_end" type="datetime"
                value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态">
          <el-select v-model="taskForm.status" style="width:100%">
            <el-option v-for="s in taskStatusOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="taskForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="taskSaving" @click="handleTaskSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
