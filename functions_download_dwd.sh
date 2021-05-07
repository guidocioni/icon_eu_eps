listurls() {
	filename="$1"
	url="$2"
	wget -qO- $url | grep -Eoi '<a [^>]+>' | \
	grep -Eo 'href="[^\"]+"' | \
	grep -Eo $filename | \
	xargs -I {} echo "$url"{}
}
export -f listurls
#
get_and_extract_one() {
  url="$1"
  file=`basename $url | sed 's/\.bz2//g'`
  if [ ! -f "$file" ]; then
  	wget -t 2 -q -O - "$url" | bzip2 -dc > "$file"
  fi
}
export -f get_and_extract_one
#################
extract_members() {
	filename="$1"
	# infer name of variable by looking inside netcdf
	name=`cdo vardes ${filename} | awk -F" " 'FNR == 1 {print $2}'`
	# ensemble members
	vals=($(seq 2 1 40))
	for i in "${vals[@]}"; do
		cdo chname,"${name}_${i}","${name}" -select,name="${name}_${i}" ${filename} ens${i}_${filename}
	done
	cdo chname,"${name}","${name}" -select,name="${name}" ${filename} ens1_${filename}
}
export -f extract_members
#################
merge_members() {
	vals=($(seq 1 1 40))
	for i in "${vals[@]}"; do
		cdo merge ens${i}_*.nc merged_ens${i}_${year}${month}${day}${run}.nc
		rm ens${i}_*.nc
	done
}
export -f merge_members
##############################################
download_merge_2d_variable_icon_eu_eps()
{
	filename="icon-eu-eps_europe_icosahedral_single-level_${year}${month}${day}${run}_*_${1}.grib2"
	filename_grep="icon-eu-eps_europe_icosahedral_single-level_${year}${month}${day}${run}_(.*)_${1}.grib2.bz2"
	url="https://opendata.dwd.de/weather/nwp/icon-eu-eps/grib/${run}/${1}/"
	if [ ! -f "${1}_${year}${month}${day}${run}_eur.nc" ]; then
		listurls $filename_grep $url | parallel -j 10 get_and_extract_one {}
		find ${filename} -empty -type f -delete # Remove empty files
		cdo -f nc setgrid,icon_grid_0028_R02B07_N02.nc -copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_eur.nc
		rm ${filename}
		extract_members ${1}_${year}${month}${day}${run}_eur.nc
		rm ${1}_${year}${month}${day}${run}_eur.nc
	fi
}
export -f download_merge_2d_variable_icon_eu_eps
################################################
download_merge_2d_variable_icon_eps()
{
	filename="icon-eps_global_icosahedral_single-level_${year}${month}${day}${run}_*_${1}.grib2"
	filename_grep="icon-eps_global_icosahedral_single-level_${year}${month}${day}${run}_(.*)_${1}.grib2.bz2"
	url="https://opendata.dwd.de/weather/nwp/icon-eps/grib/${run}/${1}/"
	if [ ! -f "${1}_${year}${month}${day}${run}.nc" ]; then
		listurls $filename_grep $url | parallel -j 10 get_and_extract_one {}
		find ${filename} -empty -type f -delete # Remove empty files
		cdo -f nc setgrid,icon_grid_0024_R02B06_G.nc -copy -mergetime ${filename} ${1}_${year}${month}${day}${run}.nc
		rm ${filename}
		extract_members ${1}_${year}${month}${day}${run}.nc
	fi
}
export -f download_merge_2d_variable_icon_eps
################################################
download_invariant_icon_eu_eps()
{
	# download grid
	filename="icon_grid_0028_R02B07_N02.nc"
	wget -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/lib/cdo/"
	bzip2 -d ${filename}.bz2
	# download hsurf
	filename="icon-eu-eps_europe_icosahedral_time-invariant_${year}${month}${day}${run}_hsurf.grib2"
	wget -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon-eu-eps/grib/${run}/hsurf/"
	bzip2 -d ${filename}.bz2 
	cdo -f nc setgrid,icon_grid_0028_R02B07_N02.nc -copy ${filename} invariant_hsurf_${year}${month}${day}${run}_eur.nc
	rm ${filename}
}
export -f download_invariant_icon_eu_eps
##############################################
download_invariant_icon_eps()
{
	# download grid
	filename="icon_grid_0024_R02B06_G.nc"
	wget -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/lib/cdo/"
	bzip2 -d ${filename}.bz2
	# download hsurf
	filename="icon-eps_global_icosahedral_time-invariant_${year}${month}${day}${run}_hsurf.grib2"
	wget -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon-eps/grib/${run}/hsurf/"
	bzip2 -d ${filename}.bz2 
	cdo -f nc setgrid,icon_grid_0024_R02B06_G.nc -copy ${filename} invariant_hsurf_${year}${month}${day}${run}_global.nc
	rm ${filename}

}
export -f download_invariant_icon_eps
################################################