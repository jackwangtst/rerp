<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { quotationApi, type QuotationListItem } from '@/api/quotation'
import { oppApi, type OppListItem } from '@/api/opportunity'
import { customerApi, type CustomerListItem, type Contact } from '@/api/customer'
import { priceCatalogApi, type PriceCatalogSearchItem } from '@/api/priceCatalog'

const loading = ref(false)
const list = ref<QuotationListItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '' })

const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  opp_id: '',
  customer_id: '',
  valid_until: '',
  discount_amount: null as number | null,
  discount_rate: null as number | null,
  status: '草稿',
  contact_name: '',
  contact_phone: '',
  deliver_to_address: '',
  product_name: '',
  product_model: '',
  payment_terms: '',
  remark: '',
  items: [] as {
    country: string; name: string; standard: string
    lr_or_not: string; months: number | null; local_testing: string; models: string
    unit_price: number; discount: number; amount: number; item_remark: string
  }[],
})
const editId = ref<string | null>(null)
const saving = ref(false)

const detailVisible = ref(false)
const activeQuot = ref<any>(null)

const statusOptions = ['草稿', '待审批', '已发送', '已接受', '已拒绝', '已过期']
const ynOptions = ['Y', 'N', '-']

// 价格库：国家列表 + 按国家加载认证项目
const countryOptions = ref<string[]>([])
const catalogByCountry = ref<Record<string, PriceCatalogSearchItem[]>>({})

async function loadCountries() {
  const res = await priceCatalogApi.countries()
  countryOptions.value = res.data
}

async function loadCatalogForCountry(country: string) {
  if (!country || catalogByCountry.value[country]) return
  const res = await priceCatalogApi.search({ country })
  catalogByCountry.value[country] = res.data
}

function onCountryChange(item: typeof form.items[0]) {
  // 切换国家时清空认证项目，并预加载该国家的项目列表
  item.name = ''
  if (item.country) loadCatalogForCountry(item.country)
}

function onCertSelect(item: typeof form.items[0], catalog: PriceCatalogSearchItem) {
  item.lr_or_not = catalog.based_on_report ?? item.lr_or_not
  item.local_testing = catalog.includes_testing ?? item.local_testing
  if (catalog.lead_weeks) item.months = Math.ceil(catalog.lead_weeks / 4.33)
  if (catalog.ref_price != null) {
    item.unit_price = Number(catalog.ref_price)
    recalcItem(item)
  }
}

function certOptionsForRow(item: typeof form.items[0]): PriceCatalogSearchItem[] {
  if (!item.country) return []
  return catalogByCountry.value[item.country] ?? []
}

const oppOptions = ref<OppListItem[]>([])
const oppLoading = ref(false)
async function searchOpps(keyword: string) {
  if (!keyword) return
  oppLoading.value = true
  try {
    const res = await oppApi.list({ keyword, page_size: 20 })
    oppOptions.value = res.data
  } finally {
    oppLoading.value = false
  }
}

const customerOptions = ref<CustomerListItem[]>([])
const contactOptions = ref<Contact[]>([])

async function loadAllCustomers() {
  const res = await customerApi.list({ page_size: 200 })
  customerOptions.value = res.data
}

async function onCustomerChange(customerId: string) {
  // 清空联系人选项和已选联系人
  contactOptions.value = []
  form.contact_name = ''
  form.contact_phone = ''

  if (!customerId) return
  const res = await customerApi.get(customerId)
  // 加载联系人列表
  contactOptions.value = res.data.contacts ?? []
  // 自动选中主联系人
  const primary = res.data.contacts?.find(c => c.is_primary)
  if (primary) {
    form.contact_name = primary.name
    form.contact_phone = primary.phone
  }
  // 收件地址为空时自动填入客户地址
  if (!form.deliver_to_address && res.data.address) {
    form.deliver_to_address = res.data.address
  }
}

function onContactSelect(name: string) {
  const contact = contactOptions.value.find(c => c.name === name)
  if (contact) {
    form.contact_phone = contact.phone
  }
}

const totalAmount = computed(() =>
  form.items.reduce((s, i) => s + (Number(i.amount) || 0), 0)
)
const finalAmount = computed(() =>
  totalAmount.value - (form.discount_amount || 0)
)

function recalcItem(item: typeof form.items[0]) {
  item.amount = Math.round(item.unit_price * item.discount * 100) / 100
}

function addItem() {
  form.items.push({
    country: '', name: '', standard: '',
    lr_or_not: 'N', months: null, local_testing: 'N', models: '',
    unit_price: 0, discount: 1, amount: 0, item_remark: '',
  })
}
function removeItem(i: number) { form.items.splice(i, 1) }

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    const res = await quotationApi.list(params as any)
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() { query.status = ''; query.page = 1; loadList() }

function openCreate() {
  editId.value = null
  oppOptions.value = []
  contactOptions.value = []
  Object.assign(form, {
    opp_id: '', customer_id: '', valid_until: '', discount_amount: null, discount_rate: null,
    status: '草稿', contact_name: '', contact_phone: '', deliver_to_address: '',
    product_name: '', product_model: '', payment_terms: '', remark: '',
    items: [{
      country: '', name: '', standard: '',
      lr_or_not: 'N', months: null, local_testing: 'N', models: '',
      unit_price: 0, discount: 1, amount: 0, item_remark: '',
    }],
  })
  dialogVisible.value = true
}

async function openEdit(row: QuotationListItem) {
  const res = await quotationApi.get(row.id)
  const d = res.data
  editId.value = d.id
  oppOptions.value = []
  contactOptions.value = []
  if (d.opp_id) {
    const oRes = await oppApi.list({ keyword: '', page_size: 50 })
    oppOptions.value = oRes.data
  }
  // 加载关联客户的联系人列表
  if (d.customer_id) {
    const cRes = await customerApi.get(d.customer_id)
    contactOptions.value = cRes.data.contacts ?? []
  }
  Object.assign(form, {
    opp_id: d.opp_id ?? '', customer_id: d.customer_id ?? '',
    valid_until: d.valid_until,
    discount_amount: (d as any).discount_amount ?? null,
    discount_rate: d.discount_rate, status: d.status,
    contact_name: (d as any).contact_name ?? '',
    contact_phone: (d as any).contact_phone ?? '',
    deliver_to_address: (d as any).deliver_to_address ?? '',
    product_name: (d as any).product_name ?? '',
    product_model: (d as any).product_model ?? '',
    payment_terms: (d as any).payment_terms ?? '',
    remark: (d as any).remark ?? '',
    items: d.items.map((i: any) => ({
      country: i.country ?? '',
      name: i.name ?? '',
      standard: i.standard ?? '',
      lr_or_not: i.lr_or_not ?? 'N',
      months: i.months ?? null,
      local_testing: i.local_testing ?? 'N',
      models: i.models ?? '',
      unit_price: Number(i.unit_price) ?? 0,
      discount: Number(i.discount) ?? 1,
      amount: Number(i.amount) ?? 0,
      item_remark: i.item_remark ?? '',
    })),
  })
  // 预加载各行国家的认证项目列表
  const countries = [...new Set(form.items.map(i => i.country).filter(Boolean))]
  countries.forEach(c => loadCatalogForCountry(c))
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = {
      ...form,
      total_amount: totalAmount.value,
      opp_id: form.opp_id || null,
      customer_id: form.customer_id || null,
      valid_until: form.valid_until || null,
      discount_amount: form.discount_amount || null,
      contact_name: form.contact_name || null,
      contact_phone: form.contact_phone || null,
      deliver_to_address: form.deliver_to_address || null,
      product_name: form.product_name || null,
      product_model: form.product_model || null,
      payment_terms: form.payment_terms || null,
      remark: form.remark || null,
      items: form.items.map(i => ({
        ...i,
        country: i.country || null,
        standard: i.standard || null,
        models: i.models || null,
        months: i.months || null,
        item_remark: i.item_remark || null,
      })),
    }
    if (editId.value) {
      await quotationApi.update(editId.value, payload as any)
      ElMessage.success('更新成功')
    } else {
      await quotationApi.create(payload as any)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: QuotationListItem) {
  await ElMessageBox.confirm(`确认删除报价单「${row.quote_no}」？`, '提示', { type: 'warning' })
  await quotationApi.delete(row.id)
  ElMessage.success('已删除')
  loadList()
}

async function viewDetail(row: QuotationListItem) {
  const res = await quotationApi.get(row.id)
  activeQuot.value = res.data
  detailVisible.value = true
}

async function exportPdf(row: any) {
  try {
    const token = localStorage.getItem('token')
    const resp = await fetch(`/api/v1/quotations/${row.id}/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!resp.ok) throw new Error('下载失败')
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${row.quote_no}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('PDF 导出失败')
  }
}

const statusTagType = (s: string) =>
  ({ '草稿': 'info', '待审批': 'warning', '已发送': '', '已接受': 'success',
     '已拒绝': 'danger', '已过期': 'danger' }[s] ?? '') as any

onMounted(() => { loadList(); loadCountries(); loadAllCustomers() })
</script>

<template>
  <div>
    <!-- 搜索栏 -->
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="4">
          <el-select v-model="query.status" placeholder="状态" clearable style="width:100%">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
        <el-col :span="14" style="text-align:right">
          <el-button type="primary" icon="Plus" @click="openCreate">新建报价</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id">
        <el-table-column prop="quote_no" label="报价单号" width="150" />
        <el-table-column prop="version" label="版本" width="60" align="center" />
        <el-table-column prop="total_amount" label="总金额(元)" width="120" align="right">
          <template #default="{ row }">{{ Number(row.total_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="discount_amount" label="优惠金额" width="100" align="right">
          <template #default="{ row }">
            {{ row.discount_amount ? Number(row.discount_amount).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="valid_until" label="有效期至" width="110" />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="110">
          <template #default="{ row }">{{ row.created_at.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link @click.stop="viewDetail(row)">查看</el-button>
            <el-button size="small" link type="primary" @click.stop="openEdit(row)">编辑</el-button>
            <el-button size="small" link type="success" @click.stop="exportPdf(row)">导出PDF</el-button>
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
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑报价' : '新建报价'" width="1200px" destroy-on-close>
      <el-form ref="formRef" :model="form" label-width="80px" :rules="{
        valid_until: [{ required: true, message: '请选择有效期' }],
      }">
        <!-- 基本信息 -->
        <el-row :gutter="16">
          <el-col :span="10">
            <el-form-item label="关联商机">
              <el-select v-model="form.opp_id" filterable remote :remote-method="searchOpps"
                :loading="oppLoading" placeholder="输入商机名称搜索（可选）" clearable style="width:100%">
                <el-option v-for="o in oppOptions" :key="o.id" :label="o.opp_name" :value="o.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="关联客户">
              <el-select v-model="form.customer_id" filterable placeholder="选择客户（可选）" clearable style="width:100%" @change="onCustomerChange">
                <el-option v-for="c in customerOptions" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="7">
            <el-form-item label="有效期至" prop="valid_until">
              <el-date-picker v-model="form.valid_until" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="7">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%">
                <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="联系人">
              <el-select
                v-if="contactOptions.length"
                v-model="form.contact_name"
                placeholder="选择联系人"
                clearable
                filterable
                style="width:100%"
                @change="onContactSelect"
              >
                <el-option
                  v-for="c in contactOptions"
                  :key="c.id"
                  :label="c.title ? `${c.name}（${c.title}）` : c.name"
                  :value="c.name"
                />
              </el-select>
              <el-input v-else v-model="form.contact_name" placeholder="客户联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联系电话">
              <el-select
                v-if="contactOptions.length"
                v-model="form.contact_phone"
                placeholder="选择电话"
                clearable
                filterable
                allow-create
                style="width:100%"
              >
                <el-option
                  v-for="c in contactOptions"
                  :key="c.id"
                  :label="`${c.name}：${c.phone}`"
                  :value="c.phone"
                />
              </el-select>
              <el-input v-else v-model="form.contact_phone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="优惠金额">
              <el-input-number v-model="form.discount_amount" :min="0" :precision="2"
                style="width:100%" controls-position="right" placeholder="0" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="24">
            <el-form-item label="收件地址">
              <el-input v-model="form.deliver_to_address" placeholder="客户收件地址（将显示在PDF DELIVER TO 栏）" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品名称">
              <el-input v-model="form.product_name" placeholder="如：智能摄像头" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品型号">
              <el-input v-model="form.product_model" placeholder="如：CAM-X100" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 报价明细 -->
        <el-divider content-position="left">报价明细</el-divider>
        <el-table :data="form.items" size="small" border>
          <el-table-column label="国家" width="120">
            <template #default="{ row }">
              <el-select
                v-model="row.country"
                size="small"
                style="width:100%"
                filterable
                allow-create
                placeholder="选择或输入"
                @change="onCountryChange(row)"
              >
                <el-option v-for="c in countryOptions" :key="c" :label="c" :value="c" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="认证项目" min-width="150">
            <template #default="{ row }">
              <el-select
                v-model="row.name"
                size="small"
                style="width:100%"
                filterable
                allow-create
                placeholder="选择认证项目"
                @change="(val: string) => { const opt = certOptionsForRow(row).find(i => i.name === val); if (opt) onCertSelect(row, opt) }"
              >
                <el-option
                  v-for="c in certOptionsForRow(row)"
                  :key="c.id"
                  :label="c.name"
                  :value="c.name"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="认证标准" width="110">
            <template #default="{ row }"><el-input v-model="row.standard" size="small" /></template>
          </el-table-column>
          <el-table-column label="LR当地代表" width="90" align="center">
            <template #default="{ row }">
              <el-select v-model="row.lr_or_not" size="small" style="width:78px">
                <el-option v-for="v in ynOptions" :key="v" :label="v" :value="v" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="周期(月)" width="78">
            <template #default="{ row }">
              <el-input-number v-model="row.months" :min="1" size="small" style="width:70px" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="本地测试" width="82" align="center">
            <template #default="{ row }">
              <el-select v-model="row.local_testing" size="small" style="width:72px">
                <el-option v-for="v in ynOptions" :key="v" :label="v" :value="v" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="型号/证书" width="110">
            <template #default="{ row }"><el-input v-model="row.models" size="small" placeholder="如：1款1证" /></template>
          </el-table-column>
          <el-table-column label="单价(元)" width="110">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="0" size="small"
                style="width:100px" @change="recalcItem(row)" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="折扣" width="85">
            <template #default="{ row }">
              <el-input-number v-model="row.discount" :min="0.1" :max="1" :step="0.05" :precision="2"
                size="small" style="width:78px" @change="recalcItem(row)" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="金额(元)" width="120" align="right">
            <template #default="{ row }">{{ Number(row.amount).toLocaleString() }}</template>
          </el-table-column>
          <el-table-column label="备注" min-width="120">
            <template #default="{ row }"><el-input v-model="row.item_remark" size="small" placeholder="明细备注" /></template>
          </el-table-column>
          <el-table-column label="" width="40" align="center">
            <template #default="{ $index }">
              <el-button link type="danger" icon="Delete" @click="removeItem($index)"
                :disabled="form.items.length === 1" />
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top:8px;display:flex;justify-content:space-between;align-items:center">
          <el-button size="small" icon="Plus" @click="addItem">添加明细</el-button>
          <div style="font-size:13px">
            合计：<b style="color:#409eff">RMB {{ totalAmount.toLocaleString() }}</b>
            <template v-if="form.discount_amount">
              &nbsp;&nbsp;优惠后：<b style="color:#c0392b">RMB {{ finalAmount.toLocaleString() }}</b>
            </template>
          </div>
        </div>

        <!-- 其他信息 -->
        <el-divider content-position="left">备注 / 付款条款</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="付款条款">
              <el-input v-model="form.payment_terms" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
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

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="detailVisible" title="报价单详情" width="860px">
      <template v-if="activeQuot">
        <el-descriptions :column="3" border size="small" style="margin-bottom:12px">
          <el-descriptions-item label="报价单号">{{ activeQuot.quote_no }}</el-descriptions-item>
          <el-descriptions-item label="版本">V{{ activeQuot.version }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(activeQuot.status)" size="small">{{ activeQuot.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="联系人">{{ activeQuot.contact_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ activeQuot.contact_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="有效期至">{{ activeQuot.valid_until }}</el-descriptions-item>
          <el-descriptions-item label="收件地址" :span="3">{{ activeQuot.deliver_to_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="总金额">
            <b style="color:#409eff">RMB {{ Number(activeQuot.total_amount).toLocaleString() }}</b>
          </el-descriptions-item>
          <el-descriptions-item label="优惠金额">
            {{ activeQuot.discount_amount ? 'RMB ' + Number(activeQuot.discount_amount).toLocaleString() : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="优惠后金额">
            <b v-if="activeQuot.discount_amount" style="color:#c0392b">
              RMB {{ (Number(activeQuot.total_amount) - Number(activeQuot.discount_amount)).toLocaleString() }}
            </b>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-table :data="activeQuot.items" size="small" border style="margin-bottom:10px">
          <el-table-column type="index" label="No" width="45" align="center" />
          <el-table-column prop="country" label="国家" width="80" align="center">
            <template #default="{ row }">{{ row.country || '-' }}</template>
          </el-table-column>
          <el-table-column prop="name" label="认证项目" min-width="120" />
          <el-table-column prop="standard" label="认证标准" width="110" align="center" />
          <el-table-column prop="lr_or_not" label="LR当地代表" width="80" align="center">
            <template #default="{ row }">{{ row.lr_or_not || '-' }}</template>
          </el-table-column>
          <el-table-column prop="months" label="周期(月)" width="70" align="center">
            <template #default="{ row }">{{ row.months || '-' }}</template>
          </el-table-column>
          <el-table-column prop="local_testing" label="本地测试" width="70" align="center">
            <template #default="{ row }">{{ row.local_testing || '-' }}</template>
          </el-table-column>
          <el-table-column prop="models" label="型号/证书" width="100" align="center">
            <template #default="{ row }">{{ row.models || '-' }}</template>
          </el-table-column>
          <el-table-column prop="amount" label="金额(元)" width="110" align="right">
            <template #default="{ row }">{{ Number(row.amount).toLocaleString() }}</template>
          </el-table-column>
        </el-table>

        <div v-if="activeQuot.payment_terms" style="font-size:13px;margin-bottom:4px">
          <b>付款条款：</b>{{ activeQuot.payment_terms }}
        </div>
        <div v-if="activeQuot.remark" style="font-size:13px">
          <b>备注：</b>{{ activeQuot.remark }}
        </div>
      </template>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="success" @click="activeQuot && exportPdf(activeQuot)">导出 PDF</el-button>
      </template>
    </el-dialog>
  </div>
</template>
