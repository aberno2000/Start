void analysis_z_hist(){
  TFile *in_file = new TFile("new_gas_expansion.root","read");
  TFile *out_file= new TFile("z_distribution.root", "recreate");

  TH1D *last_hist = (TH1D*)in_file->Get("Z hist_9");
  TH1D *prob_hist = (TH1D*)in_file->Get("probability_9");
  double scale = 1./last_hist->Integral();

  TH1D *copy_hist = (TH1D*)last_hist->Clone("Z9");
  TH1D *copy_prob = (TH1D*)prob_hist->Clone("PZ9");

  //copy_hist->Scale(scale);
  //copy_prob->Scale(scale);

  TF1 *fitFunction = new TF1("fitFunction", "[0] * exp(-x/ [1])", 0.002, 0.2);
  //TF1 *fitFunction2 = new TF1("fitFunction2", "[0] * exp(-x/[1])", 0.002, 0.15);

  //fitFunction->SetParameter(0, 0.1); 
  fitFunction->SetParameter(1, 0.05860378476277056);
  copy_hist->Fit("fitFunction", "R");
  //copy_hist->Fit("fitFunction2", "R");
  double lambda = fitFunction->GetParameter(1);
  std::cout<<"lamda:"<<lambda<<"\n";
  std::cout << "diff:"<<std::abs(lambda-0.05860378476277)/0.05860378476277<<"\n";
   
  fitFunction->Write();
  //fitFunction2->Write();
  //copy_prob->Write();
  copy_hist->Write();
 

}
