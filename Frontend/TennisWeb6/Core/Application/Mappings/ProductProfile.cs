using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using AutoMapper;
using TennisWeb6.Core.Application.Dtos;
using TennisWeb6.Core.Entities;

namespace TennisWeb6.Core.Application.Mappings {
    public class ProductProfile : Profile {
        public ProductProfile() {
            this.CreateMap<Product, ProductListDto>().ReverseMap();
        
        }
    }
}