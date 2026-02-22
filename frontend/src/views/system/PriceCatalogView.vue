<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { priceCatalogApi, type PriceCatalogItem } from '@/api/priceCatalog'

const loading = ref(false)
const list = ref<PriceCatalogItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, keyword: '' })

const dialogVisible = ref(false)
const formRef = ref()
const editId = ref<string | null>(null)
const saving = ref(false)

const ynOptions = ['Y', 'N']

const form = reactive({
  country: '',
  name: '',
  cert_type: '',
  sample_qty: null as number | null,
  based_on_report: '',
  lead_weeks: null as number | null,
  includes_testing: '',
  cert_validity_years: null as number | null,
  series_apply: '',
  ref_price: null as number | null,
  remark: '',
})

const showPrice = ref(false)

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    const res = await priceCatalogApi.list(params as any)
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() { query.keyword = ''; query.page = 1; loadList() }

function openCreate() {
  editId.value = null
  Object.assign(form, {
    country: '', name: '', cert_type: '',
    sample_qty: null, based_on_report: '', lead_weeks: null,
    includes_testing: '', cert_validity_years: null,
    series_apply: '', ref_price: null, remark: '',
  })
  dialogVisible.value = true
}

function openEdit(row: PriceCatalogItem) {
  editId.value = row.id
  Object.assign(form, {
    country: row.country ?? '',
    name: row.name,
    cert_type: row.cert_type ?? '',
    sample_qty: row.sample_qty ?? null,
    based_on_report: row.based_on_report ?? '',
    lead_weeks: row.lead_weeks ?? null,
    includes_testing: row.includes_testing ?? '',
    cert_validity_years: row.cert_validity_years ?? null,
    series_apply: row.series_apply ?? '',
    ref_price: row.ref_price ?? null,
    remark: row.remark ?? '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = {
      country: form.country || null,
      name: form.name,
      cert_type: form.cert_type || null,
      sample_qty: form.sample_qty || null,
      based_on_report: form.based_on_report || null,
      lead_weeks: form.lead_weeks || null,
      includes_testing: form.includes_testing || null,
      cert_validity_years: form.cert_validity_years || null,
      series_apply: form.series_apply || null,
      ref_price: form.ref_price || null,
      remark: form.remark || null,
    }
    if (editId.value) {
      await priceCatalogApi.update(editId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await priceCatalogApi.create(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: PriceCatalogItem) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' })
  await priceCatalogApi.delete(row.id)
  ElMessage.success('已删除')
  loadList()
}

onMounted(loadList)
</script>

<template>
  <div>
    <!-- 搜索栏 -->
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="6">
          <el-input v-model="query.keyword" placeholder="搜索认证名称或国家" clearable @keyup.enter="handleSearch" />
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
        <el-col :span="12" style="text-align:right">
          <el-button :type="showPrice ? 'warning' : 'default'" icon="View" @click="showPrice = !showPrice">
            {{ showPrice ? '隐藏价格' : '显示价格' }}
          </el-button>
          <el-button type="primary" icon="Plus" @click="openCreate">新增价格</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id" size="small">
        <el-table-column prop="country" label="国家" width="100" />
        <el-table-column prop="name" label="认证名称" min-width="140" />
        <el-table-column prop="cert_type" label="强制/自愿" width="90" align="center">
          <template #default="{ row }">{{ row.cert_type || '-' }}</template>
        </el-table-column>
        <el-table-column prop="sample_qty" label="样机" width="60" align="center">
          <template #default="{ row }">{{ row.sample_qty ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="based_on_report" label="基于报告转证" width="100" align="center">
          <template #default="{ row }">{{ row.based_on_report || '-' }}</template>
        </el-table-column>
        <el-table-column prop="lead_weeks" label="周期(周)" width="80" align="center">
          <template #default="{ row }">{{ row.lead_weeks ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="includes_testing" label="含测试" width="75" align="center">
          <template #default="{ row }">{{ row.includes_testing || '-' }}</template>
        </el-table-column>
        <el-table-column prop="cert_validity_years" label="有效期(年)" width="90" align="center">
          <template #default="{ row }">{{ row.cert_validity_years ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="series_apply" label="可系列" width="75" align="center">
          <template #default="{ row }">{{ row.series_apply || '-' }}</template>
        </el-table-column>
        <el-table-column v-if="showPrice" prop="ref_price" label="参考价(元)" width="110" align="right">
          <template #default="{ row }">
            {{ row.ref_price != null ? Number(row.ref_price).toLocaleString() : '-' }}
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
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑价格' : '新增价格'" width="680px" destroy-on-close>
      <el-form ref="formRef" :model="form" label-width="110px" :rules="{
        name: [{ required: true, message: '请填写认证名称' }],
      }">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="国家/地区">
              <el-input v-model="form.country" placeholder="如：津巴布韦" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="认证名称" prop="name">
              <el-input v-model="form.name" placeholder="如：POTRAZ认证" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="强制性/自愿性">
              <el-input v-model="form.cert_type" placeholder="如：强制性" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="样机数量">
              <el-input-number v-model="form.sample_qty" :min="1" style="width:100%" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="基于报告转证">
              <el-select v-model="form.based_on_report" clearable style="width:100%" placeholder="是否可基于CE/FCC报告">
                <el-option v-for="v in ynOptions" :key="v" :label="v" :value="v" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="认证周期(周)">
              <el-input-number v-model="form.lead_weeks" :min="1" style="width:100%" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="包含测试+转证">
              <el-select v-model="form.includes_testing" clearable style="width:100%">
                <el-option v-for="v in ynOptions" :key="v" :label="v" :value="v" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="证书有效期(年)">
              <el-input-number v-model="form.cert_validity_years" :min="1" style="width:100%" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="可系列申请">
              <el-select v-model="form.series_apply" clearable style="width:100%">
                <el-option v-for="v in ynOptions" :key="v" :label="v" :value="v" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="参考价格(元)">
              <el-input-number v-model="form.ref_price" :min="0" :precision="2" style="width:100%" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
