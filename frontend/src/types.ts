export interface PincodeInfo {
  pincode: string;
  state: string;
  district: string;
  taluka: string;
  type: 'Urban' | 'Rural' | 'Semi-Urban';
  body: string;
  ward: string;
  portal: string;
  helpline: string;
  source?: string;
}

export interface StepItem {
  step: number;
  title: string;
  detail: string;
}

export interface ActionButton {
  id: string;
  label: string;
  icon: string;
  url?: string;
}

export interface NavigatorResponse {
  query: string;
  category_id: string;
  category_title: string;
  summary: string;
  location: {
    pincode: string;
    state: string;
    district: string;
    taluka: string;
    type: 'Urban' | 'Rural' | 'Semi-Urban';
    authority: string;
    portal: string;
    helpline: string;
  };
  act_name: string;
  sla_days: number;
  compensation_clause: string;
  steps: StepItem[];
  dos: string[];
  donts: string[];
  action_buttons: ActionButton[];
}

export interface CategoryItem {
  id: string;
  name: string;
  icon: string;
  description: string;
  act_name: string;
  default_sla_days: number;
  rules: any;
}

export interface TrackedCase {
  id: string;
  title: string;
  category: string;
  pincode: string;
  location_type: string;
  authority: string;
  status: string;
  created_at: string;
  details?: any;
}
