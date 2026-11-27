# Draft: Alternaria dataset clarification request

**To:** Dr. Vitalijs Komasilovs, dataset ContactPerson
**Address:** No publicly verifiable professional email was found in the official dataset metadata; do not send until a verified address or official contact channel is available.
**Subject:** Clarification request for tomato *Alternaria protenta* hyperspectral cubes (DOI 10.71782/DATA/MODVMZ)

Dear Dr. Komasilovs,

I am reviewing the *Alternaria protenta* tomato hyperspectral dataset (DataverseLV DOI [10.71782/DATA/MODVMZ](https://doi.org/10.71782/DATA/MODVMZ)) for reproducible academic research and scientifically valid future machine-learning evaluation. The public record identifies you as its contact person. Could you please clarify the following for the three public NPZ files, `1797.npz`, `1827.npz`, and `1855.npz`?

1. Could you provide the exact wavelength vector and band centers for each cube, including the wavelength units, band order, dropped/bad bands, and which array axis is spectral?
2. What measurement units and radiometric quantity do the stored values represent? What calibration procedure was applied, and are the associated dark-current and white-reference captures and any calibration notes available?
3. Could you confirm the mapping of each file to trial, independent plant, leaf, part, replicate, and isolate, including the inoculation and acquisition dates? A sample-level metadata table would be especially helpful.
4. Are healthy-control hyperspectral cubes available, beyond the control observations represented in the metadata?
5. Are additional independent-plant cubes available, ideally covering control and inoculated groups, multiple disease-severity/progression stages, and sample-linked pathogen confirmation?
6. Are there supplementary files, sensor headers, calibration records, or other documentation that would resolve these questions?

We will keep the dataset separate from other pathogen datasets and will not interpret array values as reflectance or evaluate predictive performance without the necessary measurement and sample provenance. The goal is to make any future analysis reproducible and to avoid treating repeated leaves, captures, or pixels as independent plants.

Thank you for your time and for making the dataset available.

Best regards,
`[Your name]`
`[Institution / research group]`
`[Professional contact details]`

**Draft only:** No email has been sent and no author or repository contact form has been used.
