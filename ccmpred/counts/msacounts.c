#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <ctype.h>

#define N_ALPHA 21

void msa_count_single(double *counts, uint8_t *msa, double *weights, uint32_t nrow, uint32_t ncol) {
	// counts[i, a]
	memset(counts, 0, sizeof(double) * ncol * N_ALPHA);

	for(uint32_t n = 0; n < nrow; n++) {
		for(uint32_t i = 0; i < ncol; i++) {
			uint8_t a = msa[n * ncol + i];
			counts[i * N_ALPHA + a] += weights[n];
		}
	}
}


void msa_count_pairs(double *counts, uint8_t *msa, double *weights, uint32_t nrow, uint32_t ncol) {

	// counts[i, j, a, b]
	memset(counts, 0, sizeof(double) * ncol * ncol * N_ALPHA * N_ALPHA);

	#pragma omp parallel
	#pragma omp for nowait
	for(uint32_t ij = 0; ij < ncol * ncol; ij++) {
		uint32_t i = ij / ncol;
		uint32_t j = ij % ncol;
		for(uint32_t n = 0; n < nrow; n++) {

			uint8_t a = msa[n * ncol + i];
			uint8_t b = msa[n * ncol + j];
			counts[((i * ncol + j) * N_ALPHA + a) * N_ALPHA + b] += weights[n];
		}
	}
}

void msa_count_triplets(double *counts, uint8_t *msa, double *weights, uint32_t nrow, uint32_t ncol, uint32_t ntriplets, uint32_t *triplets) {

	// counts[t, a, b, c]
	memset(counts, 0, sizeof(double) * ntriplets * N_ALPHA * N_ALPHA * N_ALPHA);

	#pragma omp parallel
	#pragma omp for nowait
	for(uint32_t t = 0; t < ntriplets; t++) {
		uint32_t i = triplets[t * 3];
		uint32_t j = triplets[t * 3 + 1];
		uint32_t k = triplets[t * 3 + 2];

		for(uint32_t n = 0; n < nrow; n++) {
			uint8_t a = msa[n * ncol + i];
			uint8_t b = msa[n * ncol + j];
			uint8_t c = msa[n * ncol + k];
			counts[((t * N_ALPHA + a) * N_ALPHA + b) * N_ALPHA + c] += weights[n];
		}
	}

}

void msa_char_to_index(uint8_t *msa, uint32_t nrow, uint32_t ncol) {

	uint8_t amino_indices[29];

	// Make hash lookup table for amino acid characters to amino acid numbers
	// hash keys are the ASCII codes of the upper-case amino acids, modulo 29.
	// hash values are the amino acid numbers.
	//
	// aa   A  R  N  D  C  Q  E  G  H  I  L  K  M  F  P  S  T  W  Y  V  -
	// asc 65 82 78 68 67 81 69 71 72 73 76 75 77 70 80 83 84 87 89 86 45
	// mod  7 24 20 10  9 23 11 13 14 15 18 17 19 12 22 25 26  0  2 28 16
	for(uint8_t c = 0; c < 29; c++) {
		amino_indices[c] = 20;
	}

	amino_indices[ 7] =  0; // A
	amino_indices[24] =  1; // R
	amino_indices[20] =  2; // N
	amino_indices[10] =  3; // D
	amino_indices[ 9] =  4; // C
	amino_indices[23] =  5; // Q
	amino_indices[11] =  6; // E
	amino_indices[13] =  7; // G
	amino_indices[14] =  8; // H
	amino_indices[15] =  9; // I
	amino_indices[18] = 10; // L
	amino_indices[17] = 11; // K
	amino_indices[19] = 12; // M
	amino_indices[12] = 13; // F
	amino_indices[22] = 14; // P
	amino_indices[25] = 15; // S
	amino_indices[26] = 16; // T
	amino_indices[ 0] = 17; // W
	amino_indices[ 2] = 18; // Y
	amino_indices[28] = 19; // V
	amino_indices[16] = 20;	// -

	for(uint32_t n = 0; n < nrow; n++) {
		for(uint32_t i = 0; i < ncol; i++) {
			msa[n * ncol + i] = amino_indices[ toupper(msa[n * ncol + i]) % 29 ];
		}
	}

}


void msa_index_to_char(uint8_t *msa, uint32_t nrow, uint32_t ncol) {
	uint8_t char_indices[] = {'A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I', 'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V', '-' };

	for(uint32_t n = 0; n < nrow; n++) {
		for(uint32_t i = 0; i < ncol; i++) {
			msa[n * ncol + i] = char_indices[msa[n * ncol + i]];
		}
	}
}
