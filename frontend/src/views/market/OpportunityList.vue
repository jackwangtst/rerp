<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { oppApi, type OppListItem, type OppFollowUp } from '@/api/opportunity'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()

const loading = ref(false)
const list = ref<OppListItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, stage: '', keyword: '' })

const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  opp_name: '',
  company_name: '',
  stage: '初步接触',
  certification_type: '',
  estimated_amount: null as number | null,
  expected_close_date: '',
  win_probability: null as number | null,
  competitor: '',
  loss_reason: '',
  assigned_to: '',
  lead_id: null as string | null,
  customer_id: null as string | null,
})
const editId = ref<string | null>(null)
const saving = ref(false)

const drawerVisible = ref(false)
const activeOpp = ref<OppListItem | null>(null)
const followUps = ref<OppFollowUp[]>([])
const fuLoading = ref(false)
const fuForm = reactive({ follow_type: '电话', content: '', next_date: '' })
const fuSaving = ref(false)

const stageOptions = ['初步接触', '需求确认', '报价', '谈判', '赢单', '输单']
const followTypeOptions = ['电话', '拜访', '邮件', '微信', '其他']

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.stage) params.stage = query.stage
    if (query.keyword) params.keyword = query.keyword
    const res = await oppApi.list(params as any)
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() { query.stage = ''; query.keyword = ''; query.page = 1; loadList() }

function openCreate() {
  editId.value = null
  Object.assign(form, {
    opp_name: '', company_name: '', stage: '初步接触', certification_type: '',
    estimated_amount: null, expected_close_date: '', win_probability: null,
    competitor: '', loss_reason: '',
    assigned_to: authStore.user?.id ?? '',
    lead_id: null, customer_id: null,
  })
  dialogVisible.value = true
}

async function openEdit(row: OppListItem) {
  const res = await oppApi.get(row.id)
  const d = res.data
  editId.value = d.id
  Object.assign(form, {
    opp_name: d.opp_name, company_name: d.company_name, stage: d.stage,
    certification_type: d.certification_type, estimated_amount: d.estimated_amount,
    expected_close_date: d.expected_close_date ?? '', win_probability: d.win_probability,
    competitor: d.competitor ?? '', loss_reason: d.loss_reason ?? '',
    assigned_to: d.assigned_to, lead_id: d.lead_id, customer_id: d.customer_id,
  })
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload: Record<string, unknown> = { ...form }
    if (!payload.expected_close_date) payload.expected_close_date = null
    if (editId.value) {
      await oppApi.update(editId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await oppApi.create(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: OppListItem) {
  await ElMessageBox.confirm(`确认删除商机「${row.opp_name}」？`, '提示', { type: 'warning' })
  await oppApi.delete(row.id)
  ElMessage.success('已删除')
  loadList()
}

async function openDrawer(row: OppListItem) {
  activeOpp.value = row
  drawerVisible.value = true
  Object.assign(fuForm, { follow_type: '电话', content: '', next_date: '' })
  fuLoading.value = true
  try {
    const res = await oppApi.listFollowUps(row.id)
    followUps.value = res.data
  } finally {
    fuLoading.value = false
  }
}

async function addFollowUp() {
  if (!fuForm.content) { ElMessage.warning('请填写跟进内容'); return }
  if (!activeOpp.value) return
  fuSaving.value = true
  try {
    await oppApi.addFollowUp(activeOpp.value.id, { ...fuForm })
    ElMessage.success('已记录')
    Object.assign(fuForm, { follow_type: '电话', content: '', next_date: '' })
    const res = await oppApi.listFollowUps(activeOpp.value.id)
    followUps.value = res.data
    loadList()
  } finally {
    fuSaving.value = false
  }
}

const stageTagType = (s: string) =>
  ({ '初步接触': 'info', '需求确认': '', '报价': 'warning', '谈判': 'warning',
     '赢单': 'success', '输单': 'danger' }[s] ?? '') as any

onMounted(loadList)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="6">
          <el-input v-model="query.keyword" placeholder="搜索商机名称/公司" clearable @keyup.enter="handleSearch" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="query.stage" placeholder="阶段" clearable style="width:100%">
            <el-option v-for="s in stageOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
        <el-col :span="8" style="text-align:right">
          <el-button type="primary" icon="Plus" @click="openCreate">新建商机</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id">
        <el-table-column prop="opp_name" label="商机名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="company_name" label="公司名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="certification_type" label="认证类型" min-width="130" show-overflow-tooltip />
        <el-table-column prop="stage" label="阶段" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="stageTagType(row.stage)" size="small">{{ row.stage }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="estimated_amount" label="预估金额" width="110" align="right">
          <template #default="{ row }">
            {{ row.estimated_amount != null ? Number(row.estimated_amount).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="win_probability" label="赢单率" width="80" align="center">
          <template #default="{ row }">
            {{ row.win_probability != null ? `${row.win_probability}%` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="expected_close_date" label="预计关闭" width="110" />
        <el-table-column prop="created_at" label="创建时间" width="110">
          <template #default="{ row }">{{ row.created_at.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click.stop="openDrawer(row)">跟进</el-button>
            <el-button size="small" link type="primary" @click.stop="openEdit(row)">编辑</el-button>
            <el-button size="small" link type="danger" @click.stop="handleDelete(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑商机' : '新建商机'" width="700px" destroy-on-close>
      <el-form ref="formRef" :model="form" label-width="100px" :rules="{
        opp_name: [{ required: true, message: '请输入商机名称' }],
        company_name: [{ required: true, message: '请输入公司名称' }],
        certification_type: [{ required: true, message: '请输入认证类型' }],
        assigned_to: [{ required: true, message: '请输入负责人' }],
      }">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="商机名称" prop="opp_name">
              <el-input v-model="form.opp_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公司名称" prop="company_name">
              <el-input v-model="form.company_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="认证类型" prop="certification_type">
              <el-input v-model="form.certification_type" placeholder="如 ISO9001, ISO14001" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阶段">
              <el-select v-model="form.stage" style="width:100%">
                <el-option v-for="s in stageOptions" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预估金额">
              <el-input-number v-model="form.estimated_amount" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="赢单率(%)">
              <el-input-number v-model="form.win_probability" :min="0" :max="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计关闭">
              <el-date-picker v-model="form.expected_close_date" type="date" value-format="YYYY-MM-DD"
                style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="竞争对手">
              <el-input v-model="form.competitor" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="输单原因">
              <el-input v-model="form.loss_reason" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" :title="`跟进记录 - ${activeOpp?.opp_name}`" size="400px">
      <div style="padding:0 4px">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><span style="font-size:13px;font-weight:600">新增跟进</span></template>
          <el-select v-model="fuForm.follow_type" size="small" style="width:80px;margin-right:6px">
            <el-option v-for="t in followTypeOptions" :key="t" :label="t" :value="t" />
          </el-select>
          <el-date-picker v-model="fuForm.next_date" type="date" placeholder="下次跟进" size="small"
            value-format="YYYY-MM-DD" style="width:130px" />
          <el-input v-model="fuForm.content" type="textarea" :rows="3" placeholder="跟进内容..."
            style="margin-top:8px" />
          <el-button type="primary" size="small" :loading="fuSaving"
            style="margin-top:8px;width:100%" @click="addFollowUp">记录跟进</el-button>
        </el-card>
        <div v-loading="fuLoading">
          <el-timeline>
            <el-timeline-item
              v-for="fu in followUps"
              :key="fu.id"
              :timestamp="fu.created_at.slice(0, 16).replace('T', ' ')"
              placement="top"
            >
              <div style="font-size:12px">
                <el-tag size="small" style="margin-right:4px">{{ fu.follow_type }}</el-tag>
                {{ fu.content }}
                <div v-if="fu.next_date" style="color:#909399;margin-top:2px">
                  下次跟进：{{ fu.next_date }}
                </div>
              </div>
            </el-timeline-item>
            <div v-if="!fuLoading && followUps.length === 0"
              style="color:#c0c4cc;text-align:center;padding:20px 0;font-size:13px">
              暂无跟进记录
            </div>
          </el-timeline>
        </div>
      </div>
    </el-drawer>
  </div>
</template>
