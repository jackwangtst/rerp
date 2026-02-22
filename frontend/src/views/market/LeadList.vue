<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { leadApi, type LeadListItem, type LeadFollowUp } from '@/api/lead'

const loading = ref(false)
const list = ref<LeadListItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '', keyword: '' })

// ── 新建/编辑 ────────────────────────────────────────────────
const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  company_name: '',
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  source: '网络',
  industry: '',
  province: '',
  city: '',
  certification_interest: '',
  status: '待跟进',
  next_follow_up_date: '',
  remark: '',
})
const editId = ref<string | null>(null)
const saving = ref(false)

// ── 跟进抽屉 ─────────────────────────────────────────────────
const drawerVisible = ref(false)
const activeLead = ref<LeadListItem | null>(null)
const followUps = ref<LeadFollowUp[]>([])
const fuLoading = ref(false)
const fuForm = reactive({ follow_type: '电话', content: '', next_date: '' })
const fuSaving = ref(false)

const statusOptions = ['待跟进', '跟进中', '已转化', '已放弃']
const sourceOptions = ['展会', '网络', '转介绍', '电话', '其他']
const followTypeOptions = ['电话', '拜访', '邮件', '微信', '其他']

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    const res = await leadApi.list(params as any)
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
  Object.assign(form, {
    company_name: '', contact_name: '', contact_phone: '', contact_email: '',
    source: '网络', industry: '', province: '', city: '',
    certification_interest: '', status: '待跟进', next_follow_up_date: '', remark: '',
  })
  dialogVisible.value = true
}

async function openEdit(row: LeadListItem) {
  const res = await leadApi.get(row.id)
  const d = res.data
  editId.value = d.id
  Object.assign(form, {
    company_name: d.company_name,
    contact_name: d.contact_name ?? '',
    contact_phone: d.contact_phone,
    contact_email: d.contact_email ?? '',
    source: d.source,
    industry: d.industry ?? '',
    province: d.province ?? '',
    city: d.city ?? '',
    certification_interest: d.certification_interest ?? '',
    status: d.status,
    next_follow_up_date: d.next_follow_up_date ?? '',
    remark: d.remark ?? '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload: Record<string, unknown> = { ...form }
    if (!payload.next_follow_up_date) payload.next_follow_up_date = null
    if (editId.value) {
      await leadApi.update(editId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await leadApi.create(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: LeadListItem) {
  await ElMessageBox.confirm(`确认删除线索「${row.company_name}」？`, '提示', { type: 'warning' })
  await leadApi.delete(row.id)
  ElMessage.success('已删除')
  loadList()
}

// ── 跟进抽屉 ─────────────────────────────────────────────────
async function openDrawer(row: LeadListItem) {
  activeLead.value = row
  drawerVisible.value = true
  Object.assign(fuForm, { follow_type: '电话', content: '', next_date: '' })
  fuLoading.value = true
  try {
    const res = await leadApi.listFollowUps(row.id)
    followUps.value = res.data
  } finally {
    fuLoading.value = false
  }
}

async function addFollowUp() {
  if (!fuForm.content) { ElMessage.warning('请填写跟进内容'); return }
  if (!activeLead.value) return
  fuSaving.value = true
  try {
    await leadApi.addFollowUp(activeLead.value.id, { ...fuForm })
    ElMessage.success('已记录')
    Object.assign(fuForm, { follow_type: '电话', content: '', next_date: '' })
    const res = await leadApi.listFollowUps(activeLead.value.id)
    followUps.value = res.data
    loadList()
  } finally {
    fuSaving.value = false
  }
}

const statusTagType = (s: string) =>
  ({ '待跟进': 'info', '跟进中': 'primary', '已转化': 'success', '已放弃': 'danger' }[s] ?? 'info') as any

onMounted(loadList)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="6">
          <el-input v-model="query.keyword" placeholder="搜索公司名称" clearable @keyup.enter="handleSearch" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="query.status" placeholder="线索状态" clearable style="width:100%">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
        <el-col :span="8" style="text-align:right">
          <el-button type="primary" icon="Plus" @click="openCreate">新建线索</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id">
        <el-table-column prop="company_name" label="公司名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="contact_name" label="联系人" width="90" />
        <el-table-column prop="contact_phone" label="电话" width="130" />
        <el-table-column prop="source" label="来源" width="80" />
        <el-table-column prop="industry" label="行业" width="110" show-overflow-tooltip />
        <el-table-column prop="province" label="省份" width="80" />
        <el-table-column prop="certification_interest" label="意向认证" min-width="140" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="next_follow_up_date" label="下次跟进" width="110" />
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

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑线索' : '新建线索'" width="680px" destroy-on-close>
      <el-form ref="formRef" :model="form" label-width="100px" :rules="{
        company_name: [{ required: true, message: '请输入公司名称' }],
        contact_phone: [{ required: true, message: '请输入联系电话' }],
        source: [{ required: true, message: '请选择来源' }],
      }">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="公司名称" prop="company_name">
              <el-input v-model="form.company_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="form.contact_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="contact_phone">
              <el-input v-model="form.contact_phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="form.contact_email" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="来源" prop="source">
              <el-select v-model="form.source" style="width:100%">
                <el-option v-for="s in sourceOptions" :key="s" :label="s" :value="s" />
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
            <el-form-item label="行业">
              <el-input v-model="form.industry" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="意向认证">
              <el-input v-model="form.certification_interest" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="省份">
              <el-input v-model="form.province" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="城市">
              <el-input v-model="form.city" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="下次跟进">
              <el-date-picker v-model="form.next_follow_up_date" type="date" value-format="YYYY-MM-DD"
                style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 跟进抽屉 -->
    <el-drawer v-model="drawerVisible" :title="`跟进记录 - ${activeLead?.company_name}`" size="400px">
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
